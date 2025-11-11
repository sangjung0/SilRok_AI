import ray
import time

ray.init()

@ray.remote
class QueueActor:
    def __init__(self):
        self.queue = []  # 🔹 간단한 리스트 기반 큐

    def put(self, item):
        self.queue.append(item)  # 🔹 큐에 데이터 추가

    def get(self):
        if self.queue:
            return self.queue.pop(0)  # 🔹 FIFO 방식으로 꺼냄
        return None  # 🔹 비었을 경우 None 반환

@ray.remote
def producer(data, input_queue, result_queue, num_consumers):
    for item in data:
        print(f"[Producer] pushing: {item}")
        ray.get(input_queue.put.remote(item))  # 🔹 작업 큐에 데이터 입력

    for _ in range(num_consumers):
        ray.get(input_queue.put.remote("__END__"))  # 🔹 각 Consumer 종료용 신호 추가

    results = []
    while len(results) < len(data):  # 🔹 모든 결과 수거 전까지 반복
        result = ray.get(result_queue.get.remote())  # 🔹 결과 큐에서 결과 수신
        if result:
            print(f"[Producer] got result: {result}")
            results.append(result)
    return results  # 🔹 최종 결과 반환

@ray.remote
def consumer(cid, input_queue, result_queue):
    while True:
        item = ray.get(input_queue.get.remote())  # 🔹 작업 꺼내오기
        if item is None: continue
        if item == "__END__":  # 🔹 종료 신호일 경우 종료
            print(f"[Consumer {cid}] stopping")
            break
        print(f"[Consumer {cid}] processing {item}")
        time.sleep(0.2)  # 🔹 작업 시뮬레이션
        ray.get(result_queue.put.remote(f"{item} -> by {cid}"))  # 🔹 결과 전송

# 🔻 Actor 인스턴스 생성 (입력 큐, 결과 큐)
input_queue = QueueActor.remote()
result_queue = QueueActor.remote()

data = [f"task-{i}" for i in range(6)]  # 🔹 처리할 작업 리스트
num_consumers = 3  # 🔹 Consumer 개수

# 🔻 Producer 실행 (백그라운드 Task)
producer_task = producer.remote(data, input_queue, result_queue, num_consumers)

# 🔻 Consumers 병렬 실행
consumer_tasks = [consumer.remote(i, input_queue, result_queue) for i in range(num_consumers)]

# 🔻 결과 수거
results = ray.get(producer_task)
print("✅ Final Results:")
for r in results:
    print(r)
