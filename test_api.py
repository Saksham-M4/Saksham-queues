from app import app

def run():
    client = app.test_client()
    assert client.get('/api/health').status_code == 200
    print("PASS: health endpoint")

if __name__ == '__main__': run()
