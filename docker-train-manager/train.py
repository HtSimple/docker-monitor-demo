import time
import numpy as np

def train_task(task_id):
    print(f"训练任务 {task_id} 启动...")
    for i in range(50):
        arr = np.random.rand(5000, 5000)
        res = np.sum(arr)
        print(f"任务 {task_id} 迭代 {i+1}/50，结果：{res:.2f}")
        time.sleep(1)
    print(f"训练任务 {task_id} 完成！")

if __name__ == "__main__":
    import sys
    task_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    train_task(task_id)