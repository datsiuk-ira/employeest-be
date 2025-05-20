import requests
import json

BASE_URL = "https://quickchart.io/chart"

def get_chart_url(chart_config, width=500, height=300, device_pixel_ratio=1.0, format='png', background_color='transparent'):
    """
    Generates a QuickChart URL for the given chart configuration.
    """
    params = {
        'chart': json.dumps(chart_config) if isinstance(chart_config, dict) else chart_config,
        'width': width,
        'height': height,
        'bkg': background_color,
        'format': format,
        'devicePixelRatio': device_pixel_ratio,
    }
    try:
        response = requests.post(f"{BASE_URL}/create", json=params)
        response.raise_for_status()
        return response.json().get('url')
    except requests.RequestException as e:
        print(f"Error calling QuickChart API: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding QuickChart API response: {response.text}")
        return None

# if __name__ == '__main__':
#     example_config = {
#         'type': 'bar',
#         'data': {
#             'labels': ['January', 'February', 'March', 'April', 'May'],
#             'datasets': [{
#                 'label': 'Users',
#                 'data': [50, 60, 70, 180, 190]
#             }]
#         }
#     }
#     chart_url = get_chart_url(example_config)
#     if chart_url:
#         print(f"Chart URL: {chart_url}")
#     else:
#         print("Failed to generate chart URL.")