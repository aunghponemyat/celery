import redis
r = redis.Redis()

r.set("test_key", 12345)
print(type(r.get("test_key").decode('utf-8')))