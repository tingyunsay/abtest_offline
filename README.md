# abtest_offline
abtest offline , for recommend , 根据配置混合各个算法结果产生离线推荐数据灌入redis.
## 依赖 
```
python3
spark
redis

pip3 install -r requirements.txt
```
## 配置 --  base_config(主要)
### all_model - 基础算法(model)
设定基础算法model（模型），如
```python
{
	"id":18,
	"name":"cf_new",
	"version":"1.0.0",
	"source":"1",
	"struct":"zset",
	"key":"cf_songnw_songid"
}
```
新增的基础算法模型在此配置，解释各字段含义
```python
id	唯一id，添加时往后+1
name	算法名，用作解释
version	版本，暂未使用
source	单一算法的策略值，不能与混合策略重复
struct	redis中存储数据类型，一般zset
key	redis中存储的key格式，一般取得其前缀，拼接对应类型的基础数据(songid,albumid,singerid)
```
### all_rerank - 重排序策略(rerank)
设定重排序策略，一般有根据：用户模型重排序
```python
{
    "id":2,
    "name":"usermodel_rerank",
    "version":"1.0.0"
}
```
使用到的值只有id，对最终推荐的数据根据某种规则进行重排序（更符合用户喜好），但这里我们暂时没使用到此项(todo : 在线层重排序 --> 离线层)
### product - 产品线的混合策略
根据这里的配置，读取以上基础配置的算法内容，按照设定权重进行混合各个算法得到的结果，最后按照配置的key灌入redis
```python
    "linear_similar_song":{
		"name":"linear_similar_song", 	#相似歌曲
        "class":"song",				#使用哪种类型的rdd(song，album，singer)，基础数据
        "key":"abtest_simSong_songid", 		#合并策略灌入redis 的结果key
        "source":23,				#用户采集日志，反馈相关
        "rerankid":2,				#指定重排序方法
        "strategy":[				#策略  混合多种model
            {
                "modelid":18,
                "weight":2
            },
            {
                "modelid":19,
                "weight":2
            }
        ]
    }
```
### abtest分流
此部分暂时没有使用于本项目中（todo：考虑如何在离线层作这部分工作，这部分原是在在线计算的时候，按照配置的rate分流量到不同的产品线策略上，再根据日志反馈调整比重）
```python
abtest = {
    "similar_song":{
        "name":"similar_song",
        "product_strategy":[                #产品线策略
            {
                "name":"linear_similar_song",
                "rate":"50"
            },
            {
                "name":"linear_similar_song2",
                "rate":"50"
            }
        ]
    }
}
```
### 其他配置
redis配置 	--	整个项目使用单一redis配置  
字典地址	       --      目前为本地地址,需要手动拉取（todo：ftp地址或hdfs地址，拉取至本地，供后续计算）

## 使用
确保相关算法的结果数据已经导入redis中，类似如下:
```python
127.0.0.1:6379> zrange cf_songnw_545076619 0 -1 withscores
 1) "15972710"
 2) "0"
 3) "545076653"
 4) "0.00075973000000000002"
 5) "2097977"
 6) "0.017032240000000001"
 7) "15972692"
 8) "0.042312420000000003"
 9) "541249109"
10) "0.29477439999999999"
11) "566884409"
12) "0.51873546000000004"
13) "566884405"
14) "0.74039966999999995"
15) "545076365"
16) "1"

127.0.0.1:6379> zrange lrc_simiSong_545076619 0 -1 withscores
 1) "15972710"
 2) "0"
 3) "545076653"
 4) "0.00075973000000000002"
 5) "2097977"
 6) "0.017032240000000001"
 7) "15972692"
 8) "0.042312420000000003"
 9) "541249109"
10) "0.29477439999999999"
11) "566884409"
12) "0.51873546000000004"
13) "566884405"
14) "0.74039966999999995"
15) "545076365"
16) "1"
```

```python
git clone https://github.com/tingyunsay/abtest_offline.git


cd abtest_offline && python3 run.py
```
其会在根路径下创建一个data文件夹，其中存放的是spark计算得到的结果文件，从hdfs上拉取得到.  
  
相关信息在abtest_offline/ 下的log中查看，一切顺利观察redis中灌入的结果数据，在线层可直接使用这部分数据，不需要再进行在线计算
```python
127.0.0.1:6379> zrange abtest_simSong_545076619 0 -1 withscores
 1) "545076653"
 2) "0.00075973000000000002"
 3) "2097977"
 4) "0.017032240000000001"
 5) "15972692"
 6) "0.042312420000000003"
 7) "541249109"
 8) "0.29477439999999999"
 9) "566884409"
10) "0.51873546000000004"
11) "566884405"
12) "0.74039966999999995"
13) "545076365"
14) "1"
```
由于我测试的时候，灌入的基础数据的score是一样的，所以混合的结果数据也是相同的score值.

