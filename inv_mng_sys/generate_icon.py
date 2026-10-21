"""Generate high-resolution application icon for Inventory Management System."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_app_icon(output_dir: Path) -> Path:
    """Generate a modern 256x256 multi-resolution icon."""
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded container / shield
    margin = 16
    draw.rounded_rectangle(
        [margin, margin, size[0] - margin, size[1] - margin],
        radius=48,
        fill="#1e3a8a",  # Deep indigo
        outline="#3b82f6",  # Bright accent border
        width=6,
    )

    # Inventory Box 3D perspective / isometric box
    # Top face
    top_face = [(128, 60), (196, 96), (128, 132), (60, 96)]
    draw.polygon(top_face, fill="#60a5fa", outline="#1d4ed8")

    # Left face
    left_face = [(60, 96), (128, 132), (128, 204), (60, 168)]
    draw.polygon(left_face, fill="#2563eb", outline="#1d4ed8")

    # Right face
    right_face = [(128, 132), (196, 96), (196, 168), (128, 204)]
    draw.polygon(right_face, fill="#1d4ed8", outline="#1e40af")

    # Box tape / strapping (amber/gold accent)
    draw.polygon([(118, 66), (138, 77), (138, 137), (118, 126)], fill="#fbbf24")
    draw.polygon([(118, 126), (138, 137), (138, 204), (118, 204)], fill="#f59e0b")

    # Quality Q13 badge in bottom-right corner
    badge_center = (184, 184)
    r = 34
    draw.ellipse(
        [badge_center[0] - r, badge_center[1] - r, badge_center[0] + r, badge_center[1] + r],
        fill="#10b981",  # Emerald green (quality / TQM)
        outline="#ffffff",
        width=4,
    )

    # Checkmark inside badge
    check_coords = [
        (badge_center[0] - 14, badge_center[1]),
        (badge_center[0] - 4, badge_center[1] + 12),
        (badge_center[0] + 14, badge_center[1] - 10),
    ]
    draw.line(check_coords, fill="#ffffff", width=5, joint="curve")

    ico_path = output_dir / "app_icon.ico"
    png_path = output_dir / "app_icon.png"

    # Save PNG
    img.save(png_path, format="PNG")

    # Save multi-size ICO
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Generated {ico_path} and {png_path}")
    return ico_path


if __name__ == "__main__":
    create_app_icon(Path(__file__).resolve().parent)
