bl_info = {
    "name": "Aconite's Cleaner",
    "author": "Aconite0101",
    "version": (1, 6),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Aconite",
    "description": "Model cleanup tools: Shape Keys, Bones, Finger Weights",
    "category": "Rigging",
}

import bpy

# ==========================================
# 1. Properties
# ==========================================
class WeightCleanerProperties(bpy.types.PropertyGroup):

    # --- Shape Key Filter : preset checkboxes ---
    keep_breast: bpy.props.BoolProperty(
        name="Breast",
        description="Keep shape keys containing 'Breast'",
        default=True,
    )
    keep_nipple: bpy.props.BoolProperty(
        name="Nipple",
        description="Keep shape keys containing 'Nipple'",
        default=False,
    )
    keep_corset: bpy.props.BoolProperty(
        name="Corset",
        description="Keep shape keys containing 'Corset'",
        default=False,
    )

    # --- Shape Key Filter : extra free-text keywords ---
    shape_key_filter: bpy.props.StringProperty(
        name="Extra Keywords",
        description=(
            "Additional comma-separated keywords to keep. "
            "Example: body, small, hip"
        ),
        default="",
    )

    # --- Finger Cleaner ---
    finger_enum: bpy.props.EnumProperty(
        name="Finger",
        items=[
            ('Thumb',  "Thumb (โป้ง)",  ""),
            ('Index',  "Index (ชี้)",   ""),
            ('Middle', "Middle (กลาง)", ""),
            ('Ring',   "Ring (นาง)",    ""),
            ('Little', "Little (ก้อย)", ""),
        ],
        default='Index',
    )

    side_enum: bpy.props.EnumProperty(
        name="Side",
        items=[
            ('.L', "Left (ซ้าย)",  ""),
            ('.R', "Right (ขวา)", ""),
        ],
        default='.L',
    )


# ==========================================
# 2. Operators
# ==========================================

# ------------------------------------------------------------------
# 2a. Filter-based Shape Key Cleaner
# ------------------------------------------------------------------
class OBJECT_OT_filter_clean_shape_keys(bpy.types.Operator):
    bl_idname  = "object.filter_clean_shape_keys"
    bl_label   = "Delete Non-matching Shape Keys"
    bl_description = (
        "Delete all shape keys that do NOT match any checked preset "
        "or extra keyword. 'Basis' is always kept."
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.weight_cleaner_props

        # Build keyword list from checkboxes
        keywords = []
        if props.keep_breast:
            keywords.append("breast")
        if props.keep_nipple:
            keywords.append("nipple")
        if props.keep_corset:
            keywords.append("corset")

        # Add extra free-text keywords
        extra = [k.strip().lower() for k in props.shape_key_filter.split(",") if k.strip()]
        keywords.extend(extra)

        if not keywords:
            self.report({'WARNING'}, "No keywords selected or entered — nothing was deleted.")
            return {'CANCELLED'}

        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not selected_meshes:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}

        total_removed = 0
        total_kept    = 0

        for obj in selected_meshes:
            if obj.data.shape_keys is None:
                continue

            key_blocks = obj.data.shape_keys.key_blocks
            to_remove  = []

            for key in key_blocks:
                if key.name == "Basis":
                    continue
                key_lower = key.name.lower()
                if any(kw in key_lower for kw in keywords):
                    total_kept += 1
                else:
                    to_remove.append(key.name)

            for key_name in to_remove:
                kb = key_blocks.get(key_name)
                if kb:
                    obj.shape_key_remove(kb)
                    total_removed += 1

        self.report(
            {'INFO'},
            f"Done — removed {total_removed} shape key(s), kept {total_kept} matching key(s)."
        )
        return {'FINISHED'}


# ------------------------------------------------------------------
# 2b. Unused Bone Cleaner
# ------------------------------------------------------------------
class OBJECT_OT_clean_unused_bones(bpy.types.Operator):
    bl_idname  = "object.clean_unused_bones"
    bl_label   = "Clean Unused Bones"
    bl_description = "Remove zero-weight bones but keep Breast bones and important parent chains"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}

        armature = None
        for mesh in selected_objects:
            for mod in mesh.modifiers:
                if mod.type == 'ARMATURE' and mod.object:
                    armature = mod.object
                    break
            if armature:
                break

        if not armature or armature.type != 'ARMATURE':
            self.report({'WARNING'}, "No armature found in selected meshes.")
            return {'CANCELLED'}

        valid_groups = set()
        for mesh in selected_objects:
            for v in mesh.data.vertices:
                for g in v.groups:
                    if g.weight > 0:
                        try:
                            valid_groups.add(mesh.vertex_groups[g.group].name)
                        except IndexError:
                            pass

        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones    = armature.data.edit_bones
        bones_to_keep = set()

        for bone in edit_bones:
            if bone.name in valid_groups or "Breast" in bone.name:
                bones_to_keep.add(bone.name)

        for bone in edit_bones:
            if bone.name in bones_to_keep:
                parent = bone.parent
                while parent:
                    bones_to_keep.add(parent.name)
                    parent = parent.parent

        bones_to_remove = [b.name for b in edit_bones if b.name not in bones_to_keep]
        for bone_name in bones_to_remove:
            bone = edit_bones.get(bone_name)
            if bone:
                edit_bones.remove(bone)

        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, f"Removed {len(bones_to_remove)} unused bones safely.")
        return {'FINISHED'}


# ------------------------------------------------------------------
# 2c. Finger Weight Cleaner
# ------------------------------------------------------------------
class OBJECT_OT_clean_finger_weights(bpy.types.Operator):
    bl_idname  = "object.clean_finger_weights"
    bl_label   = "Keep This Finger Only"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Enter Edit Mode and select finger vertices first.")
            return {'CANCELLED'}

        props           = context.scene.weight_cleaner_props
        selected_finger = props.finger_enum.lower()
        selected_side   = props.side_enum
        fingers         = ["thumb", "index", "middle", "ring", "little"]

        if selected_side == '.L':
            side_indicators = ['.l', '_l', 'l_', 'left', '-l']
        else:
            side_indicators = ['.r', '_r', 'r_', 'right', '-r']

        target_groups_found = [
            vg.name for vg in obj.vertex_groups
            if selected_finger in vg.name.lower()
            and any(ind in vg.name.lower() for ind in side_indicators)
        ]

        if not target_groups_found:
            self.report(
                {'WARNING'},
                f"No vertex group found for {props.finger_enum} side {selected_side}."
            )
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')
        selected_verts = [v for v in obj.data.vertices if v.select]
        cleaned_count  = 0

        for v in selected_verts:
            groups_to_remove = []
            for g in v.groups:
                vg_name = obj.vertex_groups[g.group].name.lower()
                if any(f in vg_name for f in fingers):
                    is_target = selected_finger in vg_name and any(
                        ind in vg_name for ind in side_indicators
                    )
                    if not is_target:
                        groups_to_remove.append(g.group)
            for group_index in groups_to_remove:
                obj.vertex_groups[group_index].remove([v.index])
                cleaned_count += 1

        bpy.ops.object.mode_set(mode='EDIT')
        self.report(
            {'INFO'},
            f"Removed {cleaned_count} weight(s). Kept: {', '.join(target_groups_found)}"
        )
        return {'FINISHED'}


# ==========================================
# 3. UI Panels
# ==========================================

class VIEW3D_PT_shape_key_cleaner(bpy.types.Panel):
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Aconite'
    bl_label       = "Shape Key Cleaner"

    def draw(self, context):
        layout = self.layout
        props  = context.scene.weight_cleaner_props

        # ---- Preset checkboxes ----
        box = layout.box()
        box.label(text="Keep Presets:", icon='CHECKMARK')
        row = box.row(align=True)
        row.prop(props, "keep_breast", toggle=True)
        row.prop(props, "keep_nipple", toggle=True)
        row.prop(props, "keep_corset", toggle=True)

        # ---- Extra free-text ----
        box2 = layout.box()
        box2.label(text="Extra Keywords (comma separated):", icon='SORTALPHA')
        box2.prop(props, "shape_key_filter", text="")
        box2.label(text="e.g.  body, hip, small", icon='INFO')

        layout.separator()
        layout.operator(
            "object.filter_clean_shape_keys",
            text="Delete Non-matching Shape Keys",
            icon='SHAPEKEY_DATA',
        )


class VIEW3D_PT_model_cleaner(bpy.types.Panel):
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Aconite'
    bl_label       = "Model Cleaner"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.clean_unused_bones", icon='BONE_DATA')


class VIEW3D_PT_weight_cleaner(bpy.types.Panel):
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Aconite'
    bl_label       = "Finger Weight Cleaner"

    def draw(self, context):
        layout = self.layout
        props  = context.scene.weight_cleaner_props

        col = layout.column(align=True)
        col.prop(props, "finger_enum", text="Finger")
        col.prop(props, "side_enum",   text="Side")

        layout.separator()
        layout.operator(
            "object.clean_finger_weights",
            text="Keep This Finger Only",
            icon='MOD_ARMATURE',
        )


# ==========================================
# 4. Registration
# ==========================================
classes = (
    WeightCleanerProperties,
    OBJECT_OT_filter_clean_shape_keys,
    OBJECT_OT_clean_unused_bones,
    OBJECT_OT_clean_finger_weights,
    VIEW3D_PT_shape_key_cleaner,
    VIEW3D_PT_model_cleaner,
    VIEW3D_PT_weight_cleaner,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.weight_cleaner_props = bpy.props.PointerProperty(
        type=WeightCleanerProperties
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.weight_cleaner_props

if __name__ == "__main__":
    register()