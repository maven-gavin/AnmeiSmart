# Spark 实践练习集

## 练习概述

本练习集包含从基础到高级的Spark编程练习，帮助您巩固理论知识并提升实践技能。每个练习都包含详细的要求、提示和完整解答。

---

## 基础练习

### 练习1：RDD基础操作

**目标：** 熟悉RDD的创建和基本转换操作

**要求：**
1. 创建一个包含1-100数字的RDD
2. 过滤出所有质数
3. 计算质数的平方和
4. 输出结果

**提示：**
- 使用`sc.parallelize()`创建RDD
- 使用`filter()`过滤数据
- 使用`map()`进行转换
- 使用`reduce()`进行聚合

**解答：**
```scala
// 创建数字RDD
val numbers = sc.parallelize(1 to 100)

// 定义质数判断函数
def isPrime(n: Int): Boolean = {
  if (n < 2) false
  else if (n == 2) true
  else if (n % 2 == 0) false
  else {
    val sqrt = Math.sqrt(n).toInt
    (3 to sqrt by 2).forall(n % _ != 0)
  }
}

// 过滤质数并计算平方和
val primeSquares = numbers
  .filter(isPrime)
  .map(x => x * x)
  .reduce(_ + _)

println(s"质数平方和: $primeSquares")
```

### 练习2：文本处理

**目标：** 掌握文本数据的处理和分析

**要求：**
1. 读取文本文件
2. 统计单词出现频率
3. 找出出现频率最高的10个单词
4. 排除停用词（如：the, a, an, and, or, but等）

**数据：** 创建一个包含多行文本的文件`sample.txt`

**解答：**
```scala
// 读取文本文件
val textFile = sc.textFile("sample.txt")

// 定义停用词
val stopWords = Set("the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by")

// 处理文本
val wordCounts = textFile
  .flatMap(line => line.toLowerCase.split("\\W+"))
  .filter(word => word.length > 0 && !stopWords.contains(word))
  .map(word => (word, 1))
  .reduceByKey(_ + _)
  .sortBy(-_._2)
  .take(10)

// 输出结果
wordCounts.foreach { case (word, count) =>
  println(s"$word: $count")
}
```

### 练习3：DataFrame操作

**目标：** 熟悉DataFrame的创建和SQL操作

**要求：**
1. 创建一个包含学生信息的DataFrame
2. 计算每个班级的平均成绩
3. 找出成绩最高的学生
4. 统计每个班级的学生人数

**解答：**
```scala
// 导入必要的包
import org.apache.spark.sql.functions._

// 创建学生数据
case class Student(name: String, class_name: String, score: Double, age: Int)

val students = List(
  Student("Alice", "Class-A", 85.5, 18),
  Student("Bob", "Class-B", 92.0, 19),
  Student("Charlie", "Class-A", 78.5, 18),
  Student("Diana", "Class-C", 88.0, 20),
  Student("Eve", "Class-B", 95.5, 19),
  Student("Frank", "Class-A", 82.0, 18),
  Student("Grace", "Class-C", 90.5, 20)
)

val df = spark.createDataFrame(students)

// 显示数据
df.show()

// 计算每个班级的平均成绩
val avgScores = df.groupBy("class_name")
  .agg(avg("score").as("avg_score"))
  .orderBy(desc("avg_score"))

avgScores.show()

// 找出成绩最高的学生
val topStudent = df.orderBy(desc("score")).limit(1)
topStudent.show()

// 统计每个班级的学生人数
val classCounts = df.groupBy("class_name").count()
classCounts.show()
```

---

## 中级练习

### 练习4：复杂数据处理

**目标：** 处理复杂的数据结构和业务逻辑

**要求：**
1. 处理包含嵌套结构的JSON数据
2. 计算用户的行为统计
3. 生成用户画像

**数据格式：**
```json
{
  "user_id": 123,
  "name": "张三",
  "purchases": [
    {"product": "手机", "price": 3000, "date": "2023-01-15"},
    {"product": "电脑", "price": 8000, "date": "2023-02-20"}
  ],
  "visits": [
    {"page": "/home", "duration": 120, "date": "2023-01-10"},
    {"page": "/products", "duration": 300, "date": "2023-01-15"}
  ]
}
```

**解答：**
```scala
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._

// 定义schema
val schema = StructType(Array(
  StructField("user_id", IntegerType, false),
  StructField("name", StringType, false),
  StructField("purchases", ArrayType(StructType(Array(
    StructField("product", StringType, false),
    StructField("price", DoubleType, false),
    StructField("date", StringType, false)
  ))), false),
  StructField("visits", ArrayType(StructType(Array(
    StructField("page", StringType, false),
    StructField("duration", IntegerType, false),
    StructField("date", StringType, false)
  ))), false)
))

// 读取JSON数据
val df = spark.read.schema(schema).json("user_data.json")

// 计算用户画像
val userProfiles = df.select(
  col("user_id"),
  col("name"),
  size(col("purchases")).as("purchase_count"),
  size(col("visits")).as("visit_count"),
  expr("aggregate(purchases, 0D, (acc, x) -> acc + x.price)").as("total_spent"),
  expr("aggregate(visits, 0L, (acc, x) -> acc + x.duration)").as("total_duration")
)

userProfiles.show()

// 计算用户等级
val userLevels = userProfiles.withColumn("user_level",
  when(col("total_spent") >= 10000, "VIP")
    .when(col("total_spent") >= 5000, "Gold")
    .when(col("total_spent") >= 1000, "Silver")
    .otherwise("Bronze")
)

userLevels.show()
```

### 练习5：时间序列分析

**目标：** 处理时间序列数据并进行趋势分析

**要求：**
1. 处理包含时间戳的销售数据
2. 计算每日、每周、每月的销售趋势
3. 识别销售高峰期
4. 预测未来销售趋势

**解答：**
```scala
import org.apache.spark.sql.functions._
import java.sql.Timestamp

// 创建销售数据
case class Sale(product_id: Int, amount: Double, timestamp: Timestamp)

val sales = List(
  Sale(1, 100.0, Timestamp.valueOf("2023-01-01 10:00:00")),
  Sale(2, 150.0, Timestamp.valueOf("2023-01-01 14:00:00")),
  Sale(1, 200.0, Timestamp.valueOf("2023-01-02 09:00:00")),
  Sale(3, 300.0, Timestamp.valueOf("2023-01-02 16:00:00")),
  Sale(2, 120.0, Timestamp.valueOf("2023-01-03 11:00:00"))
)

val df = spark.createDataFrame(sales)

// 添加时间维度
val salesWithTime = df.withColumn("date", date_format(col("timestamp"), "yyyy-MM-dd"))
  .withColumn("hour", hour(col("timestamp")))
  .withColumn("day_of_week", dayofweek(col("timestamp")))

// 每日销售统计
val dailySales = salesWithTime.groupBy("date")
  .agg(
    sum("amount").as("daily_total"),
    count("*").as("daily_count"),
    avg("amount").as("daily_avg")
  )
  .orderBy("date")

dailySales.show()

// 每小时销售统计
val hourlySales = salesWithTime.groupBy("hour")
  .agg(
    sum("amount").as("hourly_total"),
    count("*").as("hourly_count")
  )
  .orderBy("hour")

hourlySales.show()

// 识别销售高峰期
val peakHours = hourlySales.filter(col("hourly_total") > 
  hourlySales.agg(avg("hourly_total")).first().getDouble(0))

peakHours.show()
```

### 练习6：数据清洗和转换

**目标：** 处理脏数据并进行数据质量检查

**要求：**
1. 处理包含缺失值、异常值的数据
2. 进行数据标准化
3. 检测和处理重复数据
4. 生成数据质量报告

**解答：**
```scala
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._

// 创建包含脏数据的DataFrame
val dirtyData = List(
  (1, "Alice", Some(25), Some(5000.0)),
  (2, null, Some(30), Some(6000.0)),
  (3, "Bob", None, Some(4500.0)),
  (4, "Charlie", Some(35), None),
  (5, "Alice", Some(25), Some(5000.0)), // 重复数据
  (6, "David", Some(-5), Some(100000.0)), // 异常值
  (7, "", Some(28), Some(5500.0)) // 空字符串
)

val df = spark.createDataFrame(dirtyData).toDF("id", "name", "age", "salary")

// 数据质量检查
def dataQualityReport(df: DataFrame): Unit = {
  println("=== 数据质量报告 ===")
  
  // 总行数
  val totalRows = df.count()
  println(s"总行数: $totalRows")
  
  // 缺失值统计
  df.columns.foreach { col =>
    val nullCount = df.filter(col(col).isNull).count()
    val nullPercentage = (nullCount.toDouble / totalRows) * 100
    println(s"$col 缺失值: $nullCount ($nullPercentage%)")
  }
  
  // 重复行统计
  val duplicateCount = df.count() - df.dropDuplicates().count()
  println(s"重复行数: $duplicateCount")
}

dataQualityReport(df)

// 数据清洗
val cleanedData = df
  .filter(col("name").isNotNull && length(col("name")) > 0) // 过滤空名字
  .filter(col("age").isNotNull && col("age") > 0 && col("age") < 100) // 过滤异常年龄
  .filter(col("salary").isNotNull && col("salary") > 0 && col("salary") < 100000) // 过滤异常工资
  .dropDuplicates() // 删除重复行

// 填充缺失值
val filledData = cleanedData.na.fill(Map(
  "age" -> 30,
  "salary" -> 5000.0
))

filledData.show()

// 数据标准化
val normalizedData = filledData.withColumn("normalized_salary",
  (col("salary") - filledData.agg(avg("salary")).first().getDouble(0)) /
  filledData.agg(stddev("salary")).first().getDouble(0)
)

normalizedData.show()
```

---

## 高级练习

### 练习7：机器学习集成

**目标：** 使用Spark MLlib进行机器学习任务

**要求：**
1. 加载和预处理数据
2. 进行特征工程
3. 训练分类模型
4. 评估模型性能

**解答：**
```scala
import org.apache.spark.ml.classification.{RandomForestClassifier, RandomForestClassificationModel}
import org.apache.spark.ml.evaluation.MulticlassClassificationEvaluator
import org.apache.spark.ml.feature.{VectorAssembler, StringIndexer, StandardScaler}
import org.apache.spark.ml.Pipeline

// 创建示例数据（鸢尾花数据集）
case class Iris(sepal_length: Double, sepal_width: Double, 
                petal_length: Double, petal_width: Double, species: String)

val irisData = List(
  Iris(5.1, 3.5, 1.4, 0.2, "setosa"),
  Iris(4.9, 3.0, 1.4, 0.2, "setosa"),
  Iris(7.0, 3.2, 4.7, 1.4, "versicolor"),
  Iris(6.4, 3.2, 4.5, 1.5, "versicolor"),
  Iris(6.3, 3.3, 6.0, 2.5, "virginica"),
  Iris(5.8, 2.7, 5.1, 1.9, "virginica")
)

val df = spark.createDataFrame(irisData)

// 特征工程
val labelIndexer = new StringIndexer()
  .setInputCol("species")
  .setOutputCol("label")

val featureAssembler = new VectorAssembler()
  .setInputCols(Array("sepal_length", "sepal_width", "petal_length", "petal_width"))
  .setOutputCol("features")

val scaler = new StandardScaler()
  .setInputCol("features")
  .setOutputCol("scaledFeatures")
  .setWithStd(true)
  .setWithMean(true)

// 创建模型
val rf = new RandomForestClassifier()
  .setLabelCol("label")
  .setFeaturesCol("scaledFeatures")
  .setNumTrees(10)

// 创建Pipeline
val pipeline = new Pipeline().setStages(Array(
  labelIndexer, featureAssembler, scaler, rf
))

// 分割训练和测试数据
val Array(trainingData, testData) = df.randomSplit(Array(0.8, 0.2), seed = 42)

// 训练模型
val model = pipeline.fit(trainingData)

// 预测
val predictions = model.transform(testData)

// 评估模型
val evaluator = new MulticlassClassificationEvaluator()
  .setLabelCol("label")
  .setPredictionCol("prediction")
  .setMetricName("accuracy")

val accuracy = evaluator.evaluate(predictions)
println(s"模型准确率: $accuracy")

// 显示预测结果
predictions.select("species", "label", "prediction").show()
```

### 练习8：流处理应用

**目标：** 构建实时数据处理应用

**要求：**
1. 创建模拟数据流
2. 实时处理数据
3. 计算滑动窗口统计
4. 输出实时结果

**解答：**
```scala
import org.apache.spark.streaming._
import org.apache.spark.streaming.dstream.DStream

// 创建StreamingContext
val ssc = new StreamingContext(sc, Seconds(5))

// 模拟数据流（实际应用中可能来自Kafka、Socket等）
def generateData(): String = {
  val products = List("手机", "电脑", "平板", "耳机", "手表")
  val actions = List("浏览", "购买", "收藏", "分享")
  val product = products(scala.util.Random.nextInt(products.length))
  val action = actions(scala.util.Random.nextInt(actions.length))
  s"$product,$action,${System.currentTimeMillis()}"
}

// 创建自定义Receiver
class CustomReceiver extends Receiver[String](StorageLevel.MEMORY_AND_DISK_2) {
  override def onStart(): Unit = {
    new Thread("Custom Receiver") {
      override def run(): Unit = {
        while (!isStopped()) {
          val data = generateData()
          store(data)
          Thread.sleep(1000) // 每秒生成一条数据
        }
      }
    }.start()
  }

  override def onStop(): Unit = {}
}

// 创建DStream
val lines = ssc.receiverStream(new CustomReceiver())

// 解析数据
case class UserAction(product: String, action: String, timestamp: Long)

val actions = lines.map(line => {
  val parts = line.split(",")
  UserAction(parts(0), parts(1), parts(2).toLong)
})

// 实时统计
val productStats = actions.map(action => (action.product, 1))
  .reduceByKey(_ + _)

val actionStats = actions.map(action => (action.action, 1))
  .reduceByKey(_ + _)

// 滑动窗口统计（30秒窗口，10秒滑动）
val windowedProductStats = productStats.reduceByKeyAndWindow(
  (a: Int, b: Int) => a + b,
  Seconds(30),
  Seconds(10)
)

// 输出结果
productStats.print()
actionStats.print()
windowedProductStats.print()

// 启动Streaming
ssc.start()
ssc.awaitTermination()
```

### 练习9：图计算

**目标：** 使用GraphX进行图计算

**要求：**
1. 构建社交网络图
2. 计算PageRank
3. 识别社区
4. 分析网络结构

**解答：**
```scala
import org.apache.spark.graphx._
import org.apache.spark.rdd.RDD

// 创建顶点数据（用户）
val users: RDD[(VertexId, String)] = sc.parallelize(Array(
  (1L, "Alice"),
  (2L, "Bob"),
  (3L, "Charlie"),
  (4L, "David"),
  (5L, "Eve"),
  (6L, "Frank")
))

// 创建边数据（关系）
val relationships: RDD[Edge[String]] = sc.parallelize(Array(
  Edge(1L, 2L, "friend"),
  Edge(2L, 3L, "friend"),
  Edge(3L, 1L, "friend"),
  Edge(4L, 5L, "friend"),
  Edge(5L, 6L, "friend"),
  Edge(6L, 4L, "friend"),
  Edge(1L, 4L, "colleague"),
  Edge(2L, 5L, "colleague")
))

// 创建图
val graph = Graph(users, relationships)

// 计算PageRank
val pageRank = graph.pageRank(0.001)
val pageRankVertices = pageRank.vertices

// 显示PageRank结果
pageRankVertices.join(users).collect().sortBy(-_._2._1).foreach {
  case (id, (rank, name)) => println(s"$name: $rank")
}

// 计算连通分量
val connectedComponents = graph.connectedComponents()
val componentVertices = connectedComponents.vertices

// 显示连通分量
componentVertices.join(users).collect().groupBy(_._2._1).foreach {
  case (component, vertices) =>
    println(s"组件 $component: ${vertices.map(_._2._2).mkString(", ")}")
}

// 计算三角形计数
val triangleCount = graph.triangleCount()
val triangleVertices = triangleCount.vertices

// 显示三角形计数
triangleVertices.join(users).collect().sortBy(-_._2._1).foreach {
  case (id, (count, name)) => println(s"$name: $count 个三角形")
}

// 计算度中心性
val degrees = graph.degrees
val degreeVertices = degrees.join(users).collect().sortBy(-_._2._1)

println("度中心性排名:")
degreeVertices.foreach {
  case (id, (degree, name)) => println(s"$name: $degree")
}
```

---

## 项目实战

### 项目1：电商数据分析平台

**项目目标：** 构建完整的电商数据分析系统

**功能要求：**
1. 用户行为分析
2. 商品销售分析
3. 实时推荐系统
4. 数据可视化

**实现步骤：**

#### 步骤1：数据模型设计
```scala
// 用户行为数据
case class UserBehavior(
  user_id: Long,
  item_id: Long,
  category_id: Long,
  behavior: String, // view, cart, purchase, favorite
  timestamp: Long
)

// 商品信息
case class Item(
  item_id: Long,
  category_id: Long,
  price: Double,
  brand: String,
  tags: Array[String]
)

// 用户信息
case class User(
  user_id: Long,
  age: Int,
  gender: String,
  city: String,
  register_time: Long
)
```

#### 步骤2：数据处理管道
```scala
// 数据加载和清洗
def loadAndCleanData(spark: SparkSession): (DataFrame, DataFrame, DataFrame) = {
  // 加载用户行为数据
  val behaviorDF = spark.read.json("user_behavior.json")
    .filter(col("user_id").isNotNull && col("item_id").isNotNull)
    .filter(col("behavior").isin("view", "cart", "purchase", "favorite"))
  
  // 加载商品数据
  val itemDF = spark.read.json("items.json")
    .filter(col("item_id").isNotNull && col("price") > 0)
  
  // 加载用户数据
  val userDF = spark.read.json("users.json")
    .filter(col("user_id").isNotNull)
  
  (behaviorDF, itemDF, userDF)
}

// 用户行为分析
def analyzeUserBehavior(behaviorDF: DataFrame): DataFrame = {
  behaviorDF.groupBy("user_id", "behavior")
    .agg(
      count("*").as("behavior_count"),
      max("timestamp").as("last_behavior_time")
    )
    .groupBy("user_id")
    .pivot("behavior")
    .agg(
      first("behavior_count").as("count"),
      first("last_behavior_time").as("last_time")
    )
    .na.fill(0)
}

// 商品销售分析
def analyzeItemSales(behaviorDF: DataFrame, itemDF: DataFrame): DataFrame = {
  behaviorDF.join(itemDF, "item_id")
    .filter(col("behavior") === "purchase")
    .groupBy("item_id", "category_id", "brand")
    .agg(
      count("*").as("purchase_count"),
      sum("price").as("total_revenue"),
      avg("price").as("avg_price")
    )
    .orderBy(desc("total_revenue"))
}
```

#### 步骤3：推荐系统
```scala
// 协同过滤推荐
def collaborativeFiltering(behaviorDF: DataFrame): DataFrame = {
  // 构建用户-物品矩阵
  val userItemMatrix = behaviorDF
    .filter(col("behavior") === "purchase")
    .groupBy("user_id")
    .agg(collect_list("item_id").as("purchased_items"))
  
  // 计算用户相似度
  val userSimilarity = userItemMatrix.crossJoin(userItemMatrix)
    .filter(col("user_id") =!= col("user_id_2"))
    .withColumn("similarity", calculateSimilarity(col("purchased_items"), col("purchased_items_2")))
    .filter(col("similarity") > 0.1)
  
  userSimilarity
}

// 基于内容的推荐
def contentBasedRecommendation(behaviorDF: DataFrame, itemDF: DataFrame): DataFrame = {
  // 用户偏好向量
  val userPreferences = behaviorDF
    .join(itemDF, "item_id")
    .groupBy("user_id", "category_id")
    .agg(
      count("*").as("preference_score")
    )
    .groupBy("user_id")
    .pivot("category_id")
    .agg(first("preference_score"))
    .na.fill(0)
  
  userPreferences
}
```

#### 步骤4：实时处理
```scala
// 实时用户行为处理
def processRealTimeBehavior(ssc: StreamingContext): DStream[UserBehavior] = {
  // 从Kafka读取实时数据
  val kafkaParams = Map[String, Object](
    "bootstrap.servers" -> "localhost:9092",
    "key.deserializer" -> classOf[StringDeserializer],
    "value.deserializer" -> classOf[StringDeserializer],
    "group.id" -> "ecommerce-analysis"
  )
  
  val topics = Array("user-behavior")
  val stream = KafkaUtils.createDirectStream[String, String](
    ssc, PreferConsistent, Subscribe[String, String](topics, kafkaParams)
  )
  
  // 解析数据
  stream.map(record => {
    val json = record.value()
    // 解析JSON为UserBehavior对象
    parseUserBehavior(json)
  })
}

// 实时推荐
def realTimeRecommendation(behaviorStream: DStream[UserBehavior]): DStream[(Long, List[Long])] = {
  behaviorStream
    .filter(_.behavior == "view")
    .map(behavior => (behavior.user_id, behavior.item_id))
    .groupByKey()
    .map { case (userId, itemIds) =>
      val recommendations = generateRecommendations(userId, itemIds.toList)
      (userId, recommendations)
    }
}
```

### 项目2：日志分析系统

**项目目标：** 构建企业级日志分析系统

**功能要求：**
1. 多源日志收集
2. 实时日志分析
3. 异常检测
4. 告警系统

**实现步骤：**

#### 步骤1：日志解析器
```scala
// 日志解析器
object LogParser {
  // 解析Apache访问日志
  def parseApacheLog(line: String): Option[ApacheLog] = {
    val pattern = """^(\S+) - - \[([^\]]+)\] "(\S+) (\S+) HTTP/\d\.\d" (\d+) (\d+)""".r
    line match {
      case pattern(ip, timestamp, method, url, status, bytes) =>
        Some(ApacheLog(ip, timestamp, method, url, status.toInt, bytes.toLong))
      case _ => None
    }
  }
  
  // 解析应用日志
  def parseAppLog(line: String): Option[AppLog] = {
    val pattern = """^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\S+): (.+)""".r
    line match {
      case pattern(timestamp, level, component, message) =>
        Some(AppLog(timestamp, level, component, message))
      case _ => None
    }
  }
}

case class ApacheLog(ip: String, timestamp: String, method: String, url: String, status: Int, bytes: Long)
case class AppLog(timestamp: String, level: String, component: String, message: String)
```

#### 步骤2：实时分析
```scala
// 实时日志分析
def analyzeLogs(ssc: StreamingContext): Unit = {
  // 读取多个日志源
  val apacheLogs = ssc.textFileStream("logs/apache/")
  val appLogs = ssc.textFileStream("logs/app/")
  
  // 解析Apache日志
  val parsedApacheLogs = apacheLogs.flatMap(LogParser.parseApacheLog)
  
  // 实时统计
  val requestCounts = parsedApacheLogs.map(log => (log.method, 1))
    .reduceByKey(_ + _)
  
  val statusCounts = parsedApacheLogs.map(log => (log.status, 1))
    .reduceByKey(_ + _)
  
  val ipCounts = parsedApacheLogs.map(log => (log.ip, 1))
    .reduceByKey(_ + _)
    .filter(_._2 > 100) // 过滤高频IP
  
  // 异常检测
  val errorLogs = parsedApacheLogs.filter(_.status >= 400)
  val errorRate = errorLogs.count().map(count => 
    if (count > 100) "HIGH_ERROR_RATE" else "NORMAL"
  )
  
  // 输出结果
  requestCounts.print()
  statusCounts.print()
  ipCounts.print()
  errorRate.print()
}
```

#### 步骤3：告警系统
```scala
// 告警规则
case class AlertRule(
  name: String,
  condition: String,
  threshold: Double,
  severity: String
)

// 告警检测
def detectAlerts(logStream: DStream[AppLog], rules: List[AlertRule]): DStream[Alert] = {
  logStream.flatMap(log => {
    rules.flatMap(rule => {
      if (matchesCondition(log, rule)) {
        Some(Alert(rule.name, log.timestamp, rule.severity, log.message))
      } else None
    })
  })
}

// 告警通知
def sendAlert(alert: Alert): Unit = {
  // 发送邮件、短信或Webhook
  println(s"ALERT: ${alert.name} - ${alert.severity} - ${alert.message}")
}

case class Alert(name: String, timestamp: String, severity: String, message: String)
```

---

## 性能优化练习

### 练习10：性能调优

**目标：** 优化Spark应用性能

**要求：**
1. 分析性能瓶颈
2. 优化内存使用
3. 提高并行度
4. 减少Shuffle操作

**解答：**
```scala
// 性能监控
def monitorPerformance(df: DataFrame): Unit = {
  // 缓存频繁使用的DataFrame
  df.cache()
  
  // 检查分区数
  println(s"分区数: ${df.rdd.getNumPartitions}")
  
  // 检查数据分布
  val partitionSizes = df.rdd.mapPartitions(iter => Iterator(iter.size))
  val sizes = partitionSizes.collect()
  println(s"分区大小: ${sizes.mkString(", ")}")
  
  // 检查数据倾斜
  val maxSize = sizes.max
  val minSize = sizes.min
  val skewRatio = maxSize.toDouble / minSize
  println(s"数据倾斜比例: $skewRatio")
}

// 优化分区
def optimizePartitions(df: DataFrame, targetPartitions: Int): DataFrame = {
  // 重新分区
  val repartitioned = df.repartition(targetPartitions)
  
  // 或者使用coalesce减少分区
  val coalesced = df.coalesce(targetPartitions)
  
  repartitioned
}

// 减少Shuffle
def reduceShuffle(df: DataFrame): DataFrame = {
  // 使用map-side预聚合
  df.groupBy("key")
    .agg(sum("value").as("total"))
    .filter(col("total") > 1000)
}

// 广播小表
def broadcastJoin(largeDF: DataFrame, smallDF: DataFrame): DataFrame = {
  // 广播小表
  val broadcastDF = broadcast(smallDF)
  
  largeDF.join(broadcastDF, "key")
}
```

---

## 总结

通过完成这些练习，您将掌握：

1. **基础技能**：RDD、DataFrame、Dataset的使用
2. **数据处理**：文本处理、时间序列分析、数据清洗
3. **机器学习**：特征工程、模型训练、性能评估
4. **流处理**：实时数据处理、窗口操作、状态管理
5. **图计算**：图构建、算法应用、网络分析
6. **性能优化**：内存管理、分区优化、Shuffle减少
7. **项目实战**：完整系统的设计和实现

### 学习建议

1. **循序渐进**：从基础练习开始，逐步挑战高级练习
2. **实践为主**：多动手编码，理解每个概念的实际应用
3. **项目驱动**：通过完整项目巩固所学知识
4. **性能意识**：始终关注代码的性能和可扩展性
5. **持续学习**：关注Spark社区的最新发展和最佳实践

### 扩展资源

- **官方示例**：https://github.com/apache/spark/tree/master/examples
- **性能调优指南**：https://spark.apache.org/docs/latest/tuning.html
- **最佳实践**：https://spark.apache.org/docs/latest/rdd-programming-guide.html
- **社区论坛**：https://stackoverflow.com/questions/tagged/apache-spark

---

*本练习集涵盖了Spark编程的各个方面，建议结合理论课程一起学习，通过大量实践来巩固和提升技能。*
