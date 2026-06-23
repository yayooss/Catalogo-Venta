from pocketbase import PocketBase

BASE_URL = "YOUR-IP-ADDRESS"
pb = PocketBase(BASE_URL)

def auth():
    try:
        pb.admins.auth_with_password("YOUR-EMAIL", "PASSWORD")
    except Exception as e:
        print(f"Error: {e}")