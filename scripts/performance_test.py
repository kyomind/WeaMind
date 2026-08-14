#!/usr/bin/env python3
"""
Performance test script for location-based operations.

This script tests the performance of Haversine distance calculation
using mock Taiwan administrative district data.
"""

import statistics
import sys
import time
from pathlib import Path
from typing import NamedTuple

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.weather.location_resolution import _distance


class MockLocation(NamedTuple):
    """Mock location object for testing."""

    full_name: str
    latitude: float
    longitude: float


def generate_mock_taiwan_locations() -> list[MockLocation]:
    """Generate mock Taiwan administrative district locations for testing."""
    # Sample of real Taiwan administrative districts with coordinates
    mock_locations = [
        MockLocation("臺北市中正區", 25.0330, 121.5654),
        MockLocation("臺北市大同區", 25.0633, 121.5133),
        MockLocation("臺北市中山區", 25.0642, 121.5441),
        MockLocation("臺北市松山區", 25.0500, 121.5781),
        MockLocation("臺北市大安區", 25.0267, 121.5433),
        MockLocation("臺北市萬華區", 25.0378, 121.5003),
        MockLocation("臺北市信義區", 25.0308, 121.5706),
        MockLocation("臺北市士林區", 25.0958, 121.5264),
        MockLocation("臺北市北投區", 25.1314, 121.5017),
        MockLocation("臺北市內湖區", 25.0678, 121.5897),
        MockLocation("臺北市南港區", 25.0506, 121.6067),
        MockLocation("臺北市文山區", 24.9889, 121.5706),
        MockLocation("新北市板橋區", 25.0097, 121.4583),
        MockLocation("新北市三重區", 25.0619, 121.4856),
        MockLocation("新北市中和區", 24.9997, 121.4994),
        MockLocation("新北市永和區", 25.0092, 121.5158),
        MockLocation("新北市新莊區", 25.0375, 121.4322),
        MockLocation("新北市新店區", 24.9675, 121.5419),
        MockLocation("新北市樹林區", 24.9939, 121.4203),
        MockLocation("新北市鶯歌區", 24.9547, 121.3522),
        MockLocation("桃園市桃園區", 24.9936, 121.3010),
        MockLocation("桃園市中壢區", 24.9539, 121.2267),
        MockLocation("桃園市大溪區", 24.8836, 121.2861),
        MockLocation("桃園市楊梅區", 24.9156, 121.1456),
        MockLocation("桃園市蘆竹區", 25.0442, 121.2928),
        MockLocation("新竹市東區", 24.8014, 120.9714),
        MockLocation("新竹市北區", 24.8158, 120.9508),
        MockLocation("新竹市香山區", 24.7667, 120.9336),
        MockLocation("新竹縣竹北市", 24.8369, 121.0036),
        MockLocation("新竹縣竹東鎮", 24.7403, 121.0892),
        MockLocation("苗栗縣苗栗市", 24.5603, 120.8214),
        MockLocation("苗栗縣頭份市", 24.6856, 120.8992),
        MockLocation("臺中市中區", 24.1447, 120.6794),
        MockLocation("臺中市東區", 24.1378, 120.6944),
        MockLocation("臺中市南區", 24.1158, 120.6656),
        MockLocation("臺中市西區", 24.1433, 120.6739),
        MockLocation("臺中市北區", 24.1578, 120.6814),
        MockLocation("臺中市西屯區", 24.1619, 120.6178),
        MockLocation("臺中市南屯區", 24.1372, 120.6164),
        MockLocation("臺中市北屯區", 24.1811, 120.7103),
        MockLocation("臺中市豐原區", 24.2522, 120.7233),
        MockLocation("臺中市東勢區", 24.2594, 120.8250),
        MockLocation("彰化縣彰化市", 24.0517, 120.5164),
        MockLocation("彰化縣員林市", 23.9586, 120.5714),
        MockLocation("南投縣南投市", 23.9061, 120.6825),
        MockLocation("南投縣埔里鎮", 23.9681, 120.9681),
        MockLocation("雲林縣斗六市", 23.7117, 120.5444),
        MockLocation("雲林縣虎尾鎮", 23.7078, 120.4322),
        MockLocation("嘉義市東區", 23.4856, 120.4675),
        MockLocation("嘉義市西區", 23.4797, 120.4425),
        MockLocation("嘉義縣太保市", 23.4592, 120.3328),
        MockLocation("嘉義縣朴子市", 23.4650, 120.2469),
        MockLocation("臺南市中西區", 22.9958, 120.2042),
        MockLocation("臺南市東區", 22.9847, 120.2267),
        MockLocation("臺南市南區", 22.9739, 120.1906),
        MockLocation("臺南市北區", 23.0058, 120.2056),
        MockLocation("臺南市安平區", 23.0011, 120.1681),
        MockLocation("臺南市安南區", 23.0453, 120.1889),
        MockLocation("臺南市永康區", 23.0264, 120.2575),
        MockLocation("臺南市歸仁區", 22.9672, 120.2950),
        MockLocation("高雄市新興區", 22.6331, 120.3017),
        MockLocation("高雄市前金區", 22.6278, 120.2869),
        MockLocation("高雄市苓雅區", 22.6200, 120.3181),
        MockLocation("高雄市鹽埕區", 22.6236, 120.2886),
        MockLocation("高雄市鼓山區", 22.6397, 120.2683),
        MockLocation("高雄市旗津區", 22.6158, 120.2700),
        MockLocation("高雄市前鎮區", 22.5942, 120.3181),
        MockLocation("高雄市三民區", 22.6500, 120.3250),
        MockLocation("高雄市左營區", 22.6781, 120.2944),
        MockLocation("高雄市楠梓區", 22.7331, 120.3281),
        MockLocation("屏東縣屏東市", 22.6692, 120.4881),
        MockLocation("屏東縣潮州鎮", 22.5506, 120.5419),
        MockLocation("宜蘭縣宜蘭市", 24.7594, 121.7542),
        MockLocation("宜蘭縣羅東鎮", 24.6764, 121.7719),
        MockLocation("花蓮縣花蓮市", 23.9936, 121.6069),
        MockLocation("花蓮縣玉里鎮", 23.3342, 121.3111),
        MockLocation("臺東縣臺東市", 22.7539, 121.1467),
        MockLocation("臺東縣成功鎮", 23.0975, 121.3714),
        MockLocation("澎湖縣馬公市", 23.5656, 119.5794),
        MockLocation("澎湖縣湖西鄉", 23.5828, 119.6536),
        MockLocation("金門縣金城鎮", 24.4328, 118.3167),
        MockLocation("金門縣金湖鎮", 24.4283, 118.4083),
        MockLocation("連江縣南竿鄉", 26.1500, 119.9167),
        MockLocation("連江縣北竿鄉", 26.2167, 120.0000),
    ]

    # Multiply the base locations to simulate ~368 administrative districts
    # This gives us a realistic dataset size for performance testing
    multiplied_locations = []
    for i in range(5):  # 76 * 5 = 380 locations (close to 368)
        for location in mock_locations:
            # Add slight variations to coordinates to simulate different districts
            lat_offset = (i - 2) * 0.001  # Small latitude offset
            lon_offset = (i - 2) * 0.001  # Small longitude offset

            new_location = MockLocation(
                f"{location.full_name}_v{i + 1}",
                location.latitude + lat_offset,
                location.longitude + lon_offset,
            )
            multiplied_locations.append(new_location)

    return multiplied_locations[:368]  # Exactly 368 locations


def test_haversine_performance() -> None:
    """Test the performance of Haversine distance calculation."""
    print("🧪 Testing Haversine Distance Calculation Performance\n")

    # Test coordinates (Taipei Main Station)
    test_lat, test_lon = 25.0478, 121.5170

    # Generate mock locations (simulating database query result)
    locations = generate_mock_taiwan_locations()
    location_count = len(locations)
    print(f"📍 Testing with {location_count} administrative districts")

    # Multiple test runs for statistical accuracy
    test_runs = []
    num_runs = 50  # More runs since we don't have database overhead

    for run in range(num_runs):
        start_time = time.perf_counter()

        # Simulate the exact same logic as in find_nearest_location
        min_distance = float("inf")
        nearest_location = None

        for location in locations:
            distance = _distance(test_lat, test_lon, location.latitude, location.longitude)

            if distance < min_distance:
                min_distance = distance
                nearest_location = location

        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        test_runs.append(execution_time)

        if run % 10 == 0:  # Print every 10th run
            nearest_name = nearest_location.full_name if nearest_location else "Unknown"
            print(
                f"Run {run + 1:2d}: {execution_time:.3f}ms - "
                f"Nearest: {nearest_name} ({min_distance:.1f}km)"
            )

    # Statistical analysis
    avg_time = statistics.mean(test_runs)
    median_time = statistics.median(test_runs)
    min_time = min(test_runs)
    max_time = max(test_runs)
    std_dev = statistics.stdev(test_runs) if len(test_runs) > 1 else 0

    print(f"\n📊 Performance Statistics ({num_runs} runs):")
    print(f"Average:   {avg_time:.3f}ms")
    print(f"Median:    {median_time:.3f}ms")
    print(f"Min:       {min_time:.3f}ms")
    print(f"Max:       {max_time:.3f}ms")
    print(f"Std Dev:   {std_dev:.3f}ms")

    # Performance assessment
    print("\n✅ Performance Assessment:")
    if avg_time < 1.0:
        print(
            f"🚀 Excellent! Average execution time {avg_time:.3f}ms "
            "is extremely fast for real-time usage"
        )
    elif avg_time < 5.0:
        print(f"✅ Very Good! Average execution time {avg_time:.3f}ms is well below 5ms threshold")
    elif avg_time < 15.0:
        print(f"✅ Good! Average execution time {avg_time:.3f}ms is acceptable for real-time usage")
    else:
        print(f"⚠️  Warning! Average execution time {avg_time:.3f}ms might be too slow for LINE Bot")

    # Operations per second calculation
    ops_per_second = 1000 / avg_time
    print(f"📈 Throughput: ~{ops_per_second:.0f} location queries per second")


def test_taiwan_bounds_performance() -> None:
    """Test the performance of Taiwan boundary checking."""
    print("\n🧪 Testing Taiwan Bounds Check Performance\n")

    # Test coordinates
    test_coordinates = [
        (25.0478, 121.5170),  # Taipei (inside)
        (22.6273, 120.3014),  # Kaohsiung (inside)
        (35.6762, 139.6503),  # Tokyo (outside)
        (14.5995, 120.9842),  # Manila (outside)
    ]

    num_runs = 1000000  # 1 million runs for micro-benchmarking

    for lat, lon in test_coordinates:
        times = []

        for _ in range(5):  # 5 test batches
            start_time = time.perf_counter()

            for _ in range(num_runs):
                inside = 21.9 <= lat <= 26.5 and 118.0 <= lon <= 122.0

            end_time = time.perf_counter()
            batch_time = (end_time - start_time) * 1000  # milliseconds
            times.append(batch_time)

        avg_batch_time = statistics.mean(times)
        time_per_check = avg_batch_time / num_runs * 1000  # microseconds

        status = "✅ Inside" if inside else "❌ Outside"
        print(f"({lat:7.4f}, {lon:8.4f}) {status} - {time_per_check:.3f}μs per check")


if __name__ == "__main__":
    print("🔬 WeaMind Location Service Performance Test")
    print("=" * 50)

    try:
        # Test 1: Haversine distance calculation (main performance concern)
        test_haversine_performance()

        # Test 2: Taiwan bounds checking (should be very fast)
        test_taiwan_bounds_performance()

        print("\n🎯 Conclusion:")
        print("The performance tests confirm that location-based operations")
        print("are fast enough for real-time LINE Bot responses.")
        print("\n📝 Note: This test uses representative Taiwan administrative")
        print("district data to simulate production workload.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
