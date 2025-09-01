# Spark 入门课程教案

## 课程概述

本课程旨在帮助初学者快速掌握Apache Spark的核心概念和实践技能。通过理论讲解、代码示例和实战项目，让您能够独立进行大数据处理和分析工作。

### 学习目标
- 理解Spark的核心概念和架构
- 掌握RDD、DataFrame和Dataset的使用
- 学会Spark SQL进行数据查询
- 掌握Spark Streaming处理实时数据
- 能够独立完成Spark项目开发

### 课程时长
- 理论部分：8小时
- 实践练习：12小时
- 项目实战：10小时
- 总计：30小时

---

## 第一章：Spark基础概念

### 1.1 什么是Apache Spark

Apache Spark是一个统一的大数据处理引擎，具有以下特点：

- **快速**：基于内存计算，比Hadoop MapReduce快100倍
- **易用**：支持Java、Scala、Python、R等多种语言
- **通用**：支持批处理、流处理、机器学习、图计算
- **可扩展**：可处理PB级数据

### 1.2 Spark生态系统

```
Spark Core (核心引擎)
├── Spark SQL (结构化数据处理)
├── Spark Streaming (实时流处理)
├── MLlib (机器学习库)
├── GraphX (图计算)
└── SparkR (R语言接口)
```

### 1.3 Spark架构

**集群模式架构：**
- **Driver Program**：应用程序的主进程
- **Cluster Manager**：资源管理器（YARN、Mesos、Standalone）
- **Worker Node**：执行任务的节点
- **Executor**：在Worker上运行的任务进程

### 1.4 Spark运行模式

1. **Local模式**：单机运行，用于开发和测试
2. **Standalone模式**：Spark自带的集群管理器
3. **YARN模式**：使用Hadoop YARN管理资源
4. **Mesos模式**：使用Apache Mesos管理资源

---

## 第二章：环境搭建

### 2.1 安装准备

**系统要求：**
- Java 8或更高版本
- Python 3.6+（如果使用PySpark）
- 至少4GB内存

### 2.2 下载和安装

```bash
# 下载Spark
wget https://archive.apache.org/dist/spark/spark-3.4.0/spark-3.4.0-bin-hadoop3.tgz

# 解压
tar -xzf spark-3.4.0-bin-hadoop3.tgz
cd spark-3.4.0-bin-hadoop3

# 设置环境变量
export SPARK_HOME=/path/to/spark-3.4.0-bin-hadoop3
export PATH=$PATH:$SPARK_HOME/bin
```

### 2.3 启动Spark Shell

```bash
# 启动Scala Shell
./bin/spark-shell

# 启动Python Shell
./bin/pyspark

# 启动SQL Shell
./bin/spark-sql
```

### 2.4 验证安装

```scala
// 在spark-shell中运行
val textFile = spark.read.textFile("README.md")
textFile.count()
```

---

## 第三章：RDD编程

### 3.1 RDD基础概念

RDD（Resilient Distributed Dataset）是Spark的核心数据结构：

- **Resilient**：容错性，数据丢失可自动恢复
- **Distributed**：分布式存储
- **Dataset**：数据集合

### 3.2 RDD特性

1. **不可变性**：RDD创建后不可修改
2. **分区性**：数据被分成多个分区
3. **容错性**：通过血统（lineage）恢复数据
4. **并行性**：分区可并行处理

### 3.3 创建RDD

```scala
// 从集合创建
val rdd1 = sc.parallelize(List(1, 2, 3, 4, 5))

// 从文件创建
val rdd2 = sc.textFile("data.txt")

// 从其他RDD转换
val rdd3 = rdd1.map(x => x * 2)
```

### 3.4 RDD操作

**转换操作（Transformations）：**
```scala
// map：一对一转换
val rdd = sc.parallelize(List(1, 2, 3, 4, 5))
val mapped = rdd.map(x => x * 2)

// filter：过滤
val filtered = rdd.filter(x => x > 2)

// flatMap：一对多转换
val words = sc.parallelize(List("hello world", "spark tutorial"))
val flatMapped = words.flatMap(line => line.split(" "))

// reduceByKey：按键聚合
val pairs = sc.parallelize(List(("a", 1), ("b", 1), ("a", 1)))
val reduced = pairs.reduceByKey((a, b) => a + b)
```

**行动操作（Actions）：**
```scala
// collect：收集所有元素
val result = rdd.collect()

// count：计数
val count = rdd.count()

// take：取前N个元素
val first3 = rdd.take(3)

// reduce：聚合
val sum = rdd.reduce((a, b) => a + b)
```

### 3.5 持久化

```scala
// 缓存RDD到内存
rdd.cache()

// 持久化到磁盘
rdd.persist(StorageLevel.DISK_ONLY)

// 检查点
rdd.checkpoint()
```

---

## 第四章：DataFrame和Dataset

### 4.1 DataFrame介绍

DataFrame是Spark SQL的主要数据结构，类似于关系型数据库的表：

- 具有列名和类型
- 支持SQL查询
- 自动优化执行计划

### 4.2 创建DataFrame

```scala
// 从RDD创建
val rdd = sc.parallelize(List((1, "Alice"), (2, "Bob")))
val df = rdd.toDF("id", "name")

// 从JSON文件创建
val df = spark.read.json("data.json")

// 从CSV文件创建
val df = spark.read.csv("data.csv")

// 从数据库创建
val df = spark.read.jdbc(url, table, properties)
```

### 4.3 DataFrame操作

```scala
// 显示数据
df.show()

// 显示schema
df.printSchema()

// 选择列
df.select("name", "age").show()

// 过滤数据
df.filter(df("age") > 18).show()

// 分组聚合
df.groupBy("department").agg(avg("salary")).show()

// 排序
df.orderBy(desc("salary")).show()
```

### 4.4 SQL查询

```scala
// 注册临时视图
df.createOrReplaceTempView("employees")

// 执行SQL查询
val result = spark.sql("""
  SELECT department, AVG(salary) as avg_salary
  FROM employees
  WHERE age > 25
  GROUP BY department
  ORDER BY avg_salary DESC
""")
```

### 4.5 Dataset

Dataset是DataFrame的类型安全版本：

```scala
// 定义case class
case class Person(name: String, age: Int)

// 创建Dataset
val ds = spark.createDataset(List(Person("Alice", 25), Person("Bob", 30)))

// 类型安全操作
val filtered = ds.filter(_.age > 25)
```

---

## 第五章：Spark SQL

### 5.1 Spark SQL概述

Spark SQL是Spark的SQL查询引擎，支持：

- 标准SQL查询
- HiveQL查询
- 结构化数据处理
- 与Hive集成

### 5.2 数据源

```scala
// 读取不同格式的数据
val jsonDF = spark.read.json("data.json")
val csvDF = spark.read.csv("data.csv")
val parquetDF = spark.read.parquet("data.parquet")
val orcDF = spark.read.orc("data.orc")

// 写入数据
df.write.json("output.json")
df.write.csv("output.csv")
df.write.parquet("output.parquet")
```

### 5.3 复杂查询

```sql
-- 窗口函数
SELECT 
  name,
  department,
  salary,
  ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank
FROM employees

-- 子查询
SELECT name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees)

-- 连接查询
SELECT e.name, d.department_name
FROM employees e
JOIN departments d ON e.dept_id = d.id
```

### 5.4 用户自定义函数

```scala
// 注册UDF
spark.udf.register("addOne", (x: Int) => x + 1)

// 使用UDF
spark.sql("SELECT addOne(age) as new_age FROM employees")
```

---

## 第六章：Spark Streaming

### 6.1 流处理概念

Spark Streaming将流数据分成小批次进行处理：

- **微批处理**：将流数据分成小批次
- **容错性**：支持数据丢失恢复
- **可扩展性**：支持水平扩展

### 6.2 创建Streaming应用

```scala
import org.apache.spark.streaming._

// 创建StreamingContext
val ssc = new StreamingContext(sc, Seconds(1))

// 创建DStream
val lines = ssc.socketTextStream("localhost", 9999)

// 处理数据
val words = lines.flatMap(_.split(" "))
val wordCounts = words.map(word => (word, 1)).reduceByKey(_ + _)

// 输出结果
wordCounts.print()

// 启动Streaming
ssc.start()
ssc.awaitTermination()
```

### 6.3 数据源

```scala
// Socket数据源
val lines = ssc.socketTextStream("localhost", 9999)

// 文件数据源
val lines = ssc.textFileStream("hdfs://path/to/directory")

// Kafka数据源
val kafkaParams = Map[String, Object](
  "bootstrap.servers" -> "localhost:9092",
  "key.deserializer" -> classOf[StringDeserializer],
  "value.deserializer" -> classOf[StringDeserializer],
  "group.id" -> "test-group"
)

val topics = Array("test-topic")
val stream = KafkaUtils.createDirectStream[String, String](
  ssc, PreferConsistent, Subscribe[String, String](topics, kafkaParams)
)
```

### 6.4 窗口操作

```scala
// 滑动窗口
val windowedWordCounts = wordCounts.reduceByKeyAndWindow(
  (a: Int, b: Int) => a + b,
  Seconds(30),  // 窗口长度
  Seconds(10)   // 滑动间隔
)
```

---

## 第七章：性能优化

### 7.1 内存管理

```scala
// 设置内存比例
spark.conf.set("spark.memory.fraction", "0.8")
spark.conf.set("spark.memory.storageFraction", "0.3")

// 序列化
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
```

### 7.2 分区优化

```scala
// 重新分区
val repartitioned = rdd.repartition(10)

// 合并分区
val coalesced = rdd.coalesce(5)

// 自定义分区
val customPartitioned = rdd.partitionBy(new HashPartitioner(10))
```

### 7.3 缓存策略

```scala
// 内存缓存
rdd.cache()

// 磁盘缓存
rdd.persist(StorageLevel.DISK_ONLY)

// 内存+磁盘缓存
rdd.persist(StorageLevel.MEMORY_AND_DISK)
```

### 7.4 广播变量

```scala
// 创建广播变量
val broadcastVar = sc.broadcast(Array(1, 2, 3))

// 使用广播变量
rdd.map(x => x + broadcastVar.value(0))
```

### 7.5 累加器

```scala
// 创建累加器
val accumulator = sc.longAccumulator("my-accumulator")

// 使用累加器
rdd.foreach(x => accumulator.add(x))

// 获取累加器值
println(accumulator.value)
```

---

## 第八章：实战项目

### 8.1 项目一：日志分析系统

**项目目标：** 分析Web服务器日志，统计访问量、错误率等指标

**数据格式：**
```
192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /page1 HTTP/1.1" 200 2326
```

**实现步骤：**

1. **数据加载和清洗**
```scala
val logData = sc.textFile("access.log")

// 解析日志
case class LogEntry(ip: String, timestamp: String, method: String, url: String, status: Int, bytes: Long)

val parsedLogs = logData.map(line => {
  val pattern = """^(\S+) - - \[([^\]]+)\] "(\S+) (\S+) HTTP/\d\.\d" (\d+) (\d+)""".r
  line match {
    case pattern(ip, timestamp, method, url, status, bytes) =>
      LogEntry(ip, timestamp, method, url, status.toInt, bytes.toLong)
    case _ => null
  }
}).filter(_ != null)
```

2. **统计分析**
```scala
// 按小时统计访问量
val hourlyStats = parsedLogs.map(log => {
  val hour = log.timestamp.substring(12, 14)
  (hour, 1)
}).reduceByKey(_ + _).sortByKey()

// 统计错误率
val errorCount = parsedLogs.filter(_.status >= 400).count()
val totalCount = parsedLogs.count()
val errorRate = errorCount.toDouble / totalCount

// 统计热门页面
val pageViews = parsedLogs.map(log => (log.url, 1))
  .reduceByKey(_ + _)
  .sortBy(-_._2)
  .take(10)
```

3. **结果输出**
```scala
// 保存结果
hourlyStats.saveAsTextFile("output/hourly_stats")
pageViews.saveAsTextFile("output/popular_pages")
```

### 8.2 项目二：实时推荐系统

**项目目标：** 基于用户行为数据，实时生成推荐结果

**数据格式：**
```json
{"user_id": 123, "item_id": 456, "action": "view", "timestamp": "2023-10-10T10:00:00Z"}
```

**实现步骤：**

1. **数据流处理**
```scala
val ssc = new StreamingContext(sc, Seconds(5))

// 从Kafka读取数据
val kafkaParams = Map[String, Object](
  "bootstrap.servers" -> "localhost:9092",
  "key.deserializer" -> classOf[StringDeserializer],
  "value.deserializer" -> classOf[StringDeserializer],
  "group.id" -> "recommendation-group"
)

val topics = Array("user-behavior")
val stream = KafkaUtils.createDirectStream[String, String](
  ssc, PreferConsistent, Subscribe[String, String](topics, kafkaParams)
)

// 解析JSON数据
case class UserBehavior(userId: Int, itemId: Int, action: String, timestamp: String)

val behaviors = stream.map(record => {
  val json = record.value()
  // 使用JSON库解析
  // 这里简化处理
  UserBehavior(1, 1, "view", "2023-10-10T10:00:00Z")
})
```

2. **实时推荐算法**
```scala
// 计算用户-物品相似度
val userItemMatrix = behaviors.map(b => (b.userId, b.itemId))
  .groupByKey()
  .mapValues(_.toSet)

// 基于协同过滤的推荐
def recommendItems(userId: Int, userItemMatrix: RDD[(Int, Set[Int])]): List[Int] = {
  val userItems = userItemMatrix.lookup(userId).headOption.getOrElse(Set.empty)
  
  // 找到相似用户
  val similarUsers = userItemMatrix
    .filter(_._1 != userId)
    .map { case (otherUserId, otherItems) =>
      val similarity = userItems.intersect(otherItems).size.toDouble / 
                      userItems.union(otherItems).size
      (otherUserId, similarity)
    }
    .filter(_._2 > 0.1) // 相似度阈值
    .sortBy(-_._2)
    .take(10)
  
  // 推荐相似用户喜欢的物品
  similarUsers.flatMap { case (otherUserId, _) =>
    userItemMatrix.lookup(otherUserId).headOption.getOrElse(Set.empty)
  }.toList.distinct
}
```

3. **结果输出**
```scala
// 将推荐结果写入数据库或缓存
val recommendations = behaviors.map(_.userId).distinct()
  .map(userId => (userId, recommendItems(userId, userItemMatrix)))
  .foreachRDD(rdd => {
    rdd.foreach { case (userId, items) =>
      // 写入Redis或数据库
      println(s"User $userId: ${items.mkString(", ")}")
    }
  })
```

---

## 第九章：最佳实践

### 9.1 代码组织

```scala
// 项目结构
src/
├── main/
│   ├── scala/
│   │   ├── com/company/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   ├── utils/
│   │   │   └── Main.scala
│   │   └── resources/
│   └── test/
└── build.sbt
```

### 9.2 配置管理

```scala
// 配置文件
val config = ConfigFactory.load()

// Spark配置
val sparkConf = new SparkConf()
  .setAppName("MyApp")
  .setMaster("local[*]")
  .set("spark.sql.adaptive.enabled", "true")
  .set("spark.sql.adaptive.coalescePartitions.enabled", "true")
```

### 9.3 错误处理

```scala
// 异常处理
try {
  val result = rdd.map(x => {
    if (x < 0) throw new IllegalArgumentException("Negative number")
    x * 2
  }).collect()
} catch {
  case e: Exception =>
    println(s"Error: ${e.getMessage}")
    // 记录日志或发送告警
}
```

### 9.4 监控和日志

```scala
// 添加日志
import org.apache.log4j.{Level, Logger}

Logger.getLogger("org").setLevel(Level.WARN)
Logger.getLogger("akka").setLevel(Level.WARN)

// 自定义日志
val logger = Logger.getLogger(getClass.getName)
logger.info("Processing started")
```

---

## 第十章：进阶主题

### 10.1 Spark MLlib

```scala
import org.apache.spark.ml.classification.LogisticRegression
import org.apache.spark.ml.feature.VectorAssembler

// 特征工程
val assembler = new VectorAssembler()
  .setInputCols(Array("feature1", "feature2"))
  .setOutputCol("features")

// 训练模型
val lr = new LogisticRegression()
  .setMaxIter(10)
  .setRegParam(0.3)
  .setElasticNetParam(0.8)

val model = lr.fit(trainingData)
```

### 10.2 GraphX

```scala
import org.apache.spark.graphx._

// 创建图
val vertices = sc.parallelize(Array(
  (1L, "Alice"), (2L, "Bob"), (3L, "Charlie")
))

val edges = sc.parallelize(Array(
  Edge(1L, 2L, "friend"),
  Edge(2L, 3L, "friend")
))

val graph = Graph(vertices, edges)

// 图算法
val pageRank = graph.pageRank(0.001)
```

### 10.3 Spark on Kubernetes

```yaml
# spark-submit.yaml
apiVersion: v1
kind: Pod
metadata:
  name: spark-pi
spec:
  containers:
  - name: spark
    image: spark:3.4.0
    command: ["spark-submit"]
    args:
    - "--class"
    - "org.apache.spark.examples.SparkPi"
    - "--master"
    - "k8s://https://kubernetes.default.svc"
    - "--deploy-mode"
    - "cluster"
    - "local:///opt/spark/examples/jars/spark-examples_2.12-3.4.0.jar"
```

---

## 练习和作业

### 练习1：基础RDD操作

**目标：** 熟悉RDD的基本操作

**任务：**
1. 创建一个包含1-1000数字的RDD
2. 过滤出偶数
3. 计算偶数的平方
4. 求和并输出结果

**参考答案：**
```scala
val numbers = sc.parallelize(1 to 1000)
val evenSquares = numbers
  .filter(_ % 2 == 0)
  .map(x => x * x)
  .reduce(_ + _)
println(s"Sum of even squares: $evenSquares")
```

### 练习2：DataFrame操作

**目标：** 掌握DataFrame的SQL操作

**任务：**
1. 创建一个包含员工信息的DataFrame
2. 计算每个部门的平均工资
3. 找出工资最高的员工
4. 按部门统计员工数量

**参考答案：**
```scala
case class Employee(name: String, department: String, salary: Double)
val employees = spark.createDataFrame(List(
  Employee("Alice", "IT", 5000),
  Employee("Bob", "HR", 4000),
  Employee("Charlie", "IT", 6000)
))

// 部门平均工资
employees.groupBy("department")
  .agg(avg("salary").as("avg_salary"))
  .show()

// 最高工资员工
employees.orderBy(desc("salary")).limit(1).show()

// 部门员工数量
employees.groupBy("department").count().show()
```

### 练习3：流处理应用

**目标：** 实现简单的实时数据处理

**任务：**
1. 创建一个Socket服务器发送数据
2. 使用Spark Streaming接收数据
3. 统计单词出现频率
4. 输出实时统计结果

**参考答案：**
```scala
// 启动Socket服务器（Python）
import socket
import time

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 9999))
server.listen(1)

while True:
    conn, addr = server.accept()
    conn.send(b"hello world spark streaming\n")
    time.sleep(1)
    conn.close()

// Spark Streaming应用
val ssc = new StreamingContext(sc, Seconds(1))
val lines = ssc.socketTextStream("localhost", 9999)
val words = lines.flatMap(_.split(" "))
val wordCounts = words.map(word => (word, 1)).reduceByKey(_ + _)
wordCounts.print()
ssc.start()
ssc.awaitTermination()
```

---

## 总结

通过本课程的学习，您应该已经掌握了：

1. **Spark核心概念**：RDD、DataFrame、Dataset
2. **编程技能**：Scala/Python Spark编程
3. **数据处理**：批处理、流处理、SQL查询
4. **性能优化**：内存管理、分区优化、缓存策略
5. **实战经验**：日志分析、推荐系统等实际项目

### 下一步学习建议

1. **深入学习**：
   - Spark MLlib机器学习
   - GraphX图计算
   - Spark on Kubernetes

2. **实践项目**：
   - 构建完整的数据管道
   - 参与开源项目
   - 解决实际业务问题

3. **性能调优**：
   - 学习Spark UI使用
   - 掌握性能监控工具
   - 优化大规模数据处理

4. **生态系统**：
   - 学习Hadoop生态系统
   - 了解数据湖架构
   - 掌握云原生大数据技术

### 推荐资源

- **官方文档**：https://spark.apache.org/docs/latest/
- **GitHub示例**：https://github.com/apache/spark/tree/master/examples
- **社区论坛**：https://stackoverflow.com/questions/tagged/apache-spark
- **在线课程**：Coursera、edX等平台的Spark课程

---

## 附录

### A. 常用命令

```bash
# 启动Spark Shell
./bin/spark-shell

# 提交应用
./bin/spark-submit --class com.example.MyApp myapp.jar

# 查看应用状态
./bin/spark-submit --status <app-id>

# 停止应用
./bin/spark-submit --kill <app-id>
```

### B. 配置参数

```properties
# 内存配置
spark.driver.memory=2g
spark.executor.memory=4g
spark.memory.fraction=0.8

# 并行度配置
spark.default.parallelism=200
spark.sql.shuffle.partitions=200

# 序列化配置
spark.serializer=org.apache.spark.serializer.KryoSerializer
```

### C. 常见问题

**Q: 如何处理内存不足？**
A: 增加executor内存、调整内存比例、使用磁盘缓存

**Q: 如何提高处理速度？**
A: 增加并行度、优化分区、使用广播变量

**Q: 如何处理数据倾斜？**
A: 使用自定义分区、数据预处理、两阶段聚合

---

*本课程教案由资深大数据专家编写，涵盖了Spark从入门到实战的完整内容。建议按照章节顺序学习，并结合实际项目进行练习。*
