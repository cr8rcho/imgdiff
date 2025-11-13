# Original vs Processed Statistics

## The Key Difference

### **Original Statistics**
- Based on **raw pixel differences** without any filtering
- Simply counts pixels where `diff > threshold`
- Includes **all noise and small artifacts**
- Formula: Count pixels where any RGB channel differs by more than threshold

### **Processed Statistics**
- Based on **OpenCV-filtered mask** (same process used to create the red highlight image)
- Applies:
  1. **Morphological operations** (erosion + dilation) → removes small noise
  2. **Gaussian blur** (optional) → smooths edges
- Matches **exactly what you see** in the red highlighted areas of `diff_highlight.png`
- More accurate representation of **meaningful changes**

## Visual Example

```
Original Image 1:  ████████████████
Original Image 2:  ████▓▓██████▓███  (▓ = changed pixels)
                       ↓
Raw Difference:    ....▓▓......▓...  (original sees 3 changed pixels)
                       ↓ OpenCV filtering
Processed Mask:    ....▓▓..........  (processed sees 2 changed pixels - noise removed)
                       ↓
Highlight Image:   [gray]██[red]██[gray]██████  (RED matches processed)
```

## Real Numbers from Test

```
Test case: 100x100 image with small noise + large change area

Original Statistics:
  - Changed pixels: 908 (9.08%)
  - Includes tiny 2x2 noise dots

Processed Statistics (morphology kernel=5):
  - Changed pixels: 888 (8.88%)
  - Noise dots removed, only significant changes remain

Difference: 20 pixels (2.2% reduction)
```

## Why This Matters

### Problem (Before Fix):
```json
stats.json: { "changed_percentage": 9.08% }
```
But the `diff_highlight.png` image only shows **8.88%** in red!
❌ **Mismatch!**

### Solution (After Fix):
```json
{
  "original": { "changed_percentage": 9.08% },
  "processed": { "changed_percentage": 8.88% }  ← matches image!
}
```
✅ **Aligned!**

## When to Use Each

| Use Case | Recommended |
|----------|-------------|
| **Accurate comparison with visual output** | `processed` |
| **Strict pixel-by-pixel analysis** | `original` |
| **Matching stats to diff_highlight.png** | `processed` ✓ |
| **Scientific/research purposes** | Both (for transparency) |

## Code Behavior

### In `imgdiff_googlesheet_url.py`:

```python
# Calculates BOTH
stats_original = comparator.get_statistics(threshold=20)
stats_processed = comparator.get_processed_statistics(
    threshold=20,
    morphology_kernel_size=3,  # ← applies filtering
    blur_kernel_size=0
)

# Saves BOTH to stats.json
combined_stats = {
    'original': stats_original,
    'processed': stats_processed  # ← matches red areas
}

# But Google Sheets gets ONLY processed
result['diff_percentage'] = stats_processed['diff_percentage']
```

## Parameters That Affect Processed

- **threshold**: Higher = less sensitive (both original & processed)
- **morphology_kernel_size**: Larger = more noise removal (processed only)
- **blur_kernel_size**: Larger = smoother edges (processed only)

Example:
```bash
# More aggressive filtering (removes more noise)
--threshold 30 --morphology-kernel-size 5 --blur-kernel-size 5

# Conservative filtering (keeps more detail)
--threshold 20 --morphology-kernel-size 3 --blur-kernel-size 0
```

## Summary

- **Original** = Raw mathematical difference
- **Processed** = What you actually see in the red highlighted image
- **Current behavior**: Google Sheets shows **processed** values (which is correct!)
