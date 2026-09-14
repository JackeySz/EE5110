"""Illustrate the intended single-pixel public contract.

This example intentionally raises NotImplementedError until Algorithm A and B
complete their assigned modules.
"""

from event_camera_simulator.pixel_model import detect_pixel_crossings


def main() -> None:
    result = detect_pixel_crossings(
        start_log_intensity=0.0,
        end_log_intensity=0.65,
        start_time=0.0,
        end_time=1.0,
        reference_log_intensity=0.0,
        threshold_on=0.2,
        threshold_off=0.2,
    )
    print(result)


if __name__ == "__main__":
    main()
