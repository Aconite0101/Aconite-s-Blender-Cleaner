A quality-of-life Blender addon for cleaning up mesh data after common rigging workflows — shape key filtering, bone cleanup, and finger weight isolation, all from a tidy N-panel sidebar.

---

## Features

### Shape Key Cleaner
Clean up shape keys after using **Mesh Data Transfer** from a character body to clothing. Instead of manually hunting through a long list of blendshapes, just tick what you want to keep and delete the rest in one click.

- **Preset toggles** — one-click checkboxes for `Breast`, `Nipple`, and `Corset`
- **Extra keyword field** — type any additional keywords (comma-separated) like `body, hip, small`
- **Case-insensitive substring match** — `breast` will match `Breasts_big`, `Breasts_small`, `BreastsLarge`, etc.
- `Basis` is always protected and will never be deleted

### Model Cleaner
- **Clean Unused Bones** — removes zero-weight bones from the armature while safely keeping Breast bones and all parent chains intact

### Finger Weight Cleaner
- Select which finger and side (Left / Right) you want to keep
- In Edit Mode with vertices selected, removes all other finger weights from those verts
- Auto-scans to confirm the target vertex group exists before making any changes
  
<img width="220" height="409" alt="Screenshot 2026-04-01 164051" src="https://github.com/user-attachments/assets/b485d7b5-07f9-40b5-b27a-eafc480f5378" />

---

## Installation

1. Download `aconite_cleaner.py`
2. In Blender, go to **Edit → Preferences → Add-ons → Install**
3. Select the downloaded `.py` file
4. Enable the addon by ticking the checkbox next to **"Aconite's Cleaner"**
5. Open the N-panel in the 3D Viewport (`N` key) and look for the **Aconite** tab

**Blender version:** 3.0.0 and above

---

## Usage

### Cleaning shape keys after Mesh Data Transfer

This is the main use case the addon was built for. When you transfer shape keys from a body mesh to a clothing mesh, the cloth ends up with every single blendshape — including ones that have no effect on it. This tool lets you strip those down fast.

1. Select your clothing mesh
2. Go to the **Aconite** tab in the N-panel
3. Under **Shape Key Cleaner**, tick the keywords you want to keep (e.g. `Breast`, `Corset`)
4. Optionally type extra keywords in the text field
5. Click **Delete Non-matching Shape Keys**

### Cleaning finger weights

Useful when painting weights on gloves or sleeve cuffs that only need one finger's influence.

1. In **Edit Mode**, select the vertices you want to clean
2. Under **Finger Weight Cleaner**, choose the finger and side
3. Click **Keep This Finger Only**

---

## Panels

| Panel | Location |
|---|---|
| Shape Key Cleaner | Aconite → Shape Key Cleaner |
| Model Cleaner | Aconite → Model Cleaner |
| Finger Weight Cleaner | Aconite → Finger Weight Cleaner |

---

Built for personal VRChat / VRM rigging workflows.
