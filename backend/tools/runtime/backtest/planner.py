from datetime import timedelta


def generate_windows(start, end, train_days, test_days, step):
    windows = []
    cursor = start

    while cursor + timedelta(days=train_days + test_days) <= end:
        train_start = cursor
        train_end = cursor + timedelta(days=train_days)
        test_start = train_end
        test_end = test_start + timedelta(days=test_days)

        windows.append(
            {
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end,
            }
        )
        cursor += timedelta(days=step)

    return windows
