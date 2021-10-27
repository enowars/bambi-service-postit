import multiprocessing

worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
bind = "0.0.0.0:3031"
timeout = 90
keepalive = 3600
preload_app = True
# max_requests = 200
# max_requests_jitter = 30
