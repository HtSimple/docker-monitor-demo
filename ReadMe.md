## 项目简介

这是小河豚的docker资源消耗监测的demo。

## 实现技术

cadvisor + prometheus + grafana

三个工具作用如下：

1. cAdvisor：容器数据采集器，实时采集容器 CPU、内存等指标，以 Prometheus 兼容格式暴露，轻量无依赖；
2. Prometheus：时序数据库 + 查询引擎，拉取存储数据，用 PromQL 计算 / 聚合指标，支持告警配置；
3. Grafana：可视化面板，对接 Prometheus，通过预制 / 自定义模板将数据转为直观图表，支持告警展示。

如果不要可视化面板可以不用Grafana。

## 项目结构

```plaintext
docker-monitor-demo/  # 项目根目录
├── .gitignore               # Git忽略规则
├── README.md                # 项目说明文档
├── requirements.txt         # Python依赖清单（虚拟环境用）
├── docker-train-manager/  	# 训练任务管理
│   ├── metrics_export/      # 训练容器的监控数据导出文件（自动生成）
│   ├── docker_manager.py    # 管理Docker训练容器（创建/销毁/构建镜像）
│   ├── Dockerfile           # 打包训练环境的镜像配置
│   ├── export_metrics.py    # 导出训练容器的资源使用数据
│   ├── run_train_task.py    # 一键启动训练任务的入口
│   └── train.py             # 实际的训练代码
└── monitor/   # 监控组件
    ├── data/                # 监控数据持久化
    │   ├── grafana/         # Grafana的配置、仪表盘数据
    │   └── prometheus/      # Prometheus采集的容器指标数据
    └── docker-compose.yml   # 启动监控工具（Prometheus/Grafana/cAdvisor）的配置
```

## 运行常用指令

#### 运行容器

```
// 在项目路径下，如docker-monitor-demo，开启容器
docker compose up -d
```

#### 验证是否已全部加入网络


```bash
// 查看当前网络
docker network inspect docker-monitor-demo_monitor-network | grep -E "Name|IPv4Address"
```

正常输出如下：

        "Name": "docker-monitor-demo_monitor-network",
                "Name": "grafana",
                "IPv4Address": "172.18.0.3/16",
                "Name": "cadvisor",
                "IPv4Address": "172.18.0.2/16",
                "Name": "prometheus",
                "IPv4Address": "172.18.0.4/16",

如果没有三个容器，可能是出现权限问题需要解决，如Prometheus 数据目录权限不足，需要关闭容器后添加权限再重启容器。

```bash
# 1. 停止 Prometheus 容器
docker compose stop prometheus

# 2. 给宿主机 data/prometheus 目录赋最大权限
sudo chmod -R 777 ./data/prometheus

# 3. 强制重建 Prometheus 容器
docker compose up -d --force-recreate prometheus
```

#### 运行任务并监控

在项目训练任务目录下，如docker-monitor-demo/docker-train-manager

```
// 运行任务并输出资源监控情况
python3 run_train_task.py --task-id test-001
```

