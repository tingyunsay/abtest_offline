#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os,re
from pyspark import SparkConf, SparkContext
import logging
import redis 
from conf.base_config import *
from conf.redis_conf import *
from operator import add
import subprocess
import datetime

file_name = __file__.split('/')[-1].replace(".py","")
logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='%s.log'%file_name,
                filemode='a')

#将日志打印到标准输出（设定在某个级别之上的错误）
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)-16s: %(levelname)-6s line:[%(lineno)s] %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

APP_NAME = "Tingyun Abtest Spark"

#r = redis.Redis(redis_ip, redis_port, db=0)

def get_redis(pre,word):
    r = redis.Redis(redis_ip, redis_port, db=0)
    key = pre + word
    r_con = r.zrange(key,0,-1,withscores=True)
    return r_con

#对redis中取出的（tuple）list列表的key均添加 前缀，方便后续计算
def add_pre(k,v):
    res = []
    for i in v:
        tmp = (k + "_"+i[0].decode() , i[1])
        res.append(tmp)
    return res

class ABTest(object):
    def __init__(self):
        self.author = "tingyun"
        self.allmodel = self.parse_config()
        self.allrerank = all_rerank 
        self.product = product_strategy 
        #local模式(暂时使用此模式)，集群模式需要搭建hadoop
        #串行执行多个产品线任务时候会报错，spark当前只能存在一个实例
        try:
            self.sc = SparkContext("local","APP_NAME")
        except Exception as e:
            self.sc = SparkContext.getOrCreate()
        #conf = SparkConf().setAppName(APP_NAME).setMaster("spark://127.0.0.1:7077")
        #self.sc = SparkContext(conf=conf)
        #歌词库
        self.song_dict =  self.load_dict("song")
        #专辑库
        self.album_dict =  self.load_dict("album")
        #歌手库
        self.singer_dict =  self.load_dict("singer")
        
        
        self.redis = redis.Redis(redis_ip, redis_port, db=0)

        #保存本地数据文件夹
        self.DATA_DIR = "data"

        #结果文件默认先保存到hdfs上，需要使用自行拉取
        self.hdfs_pre = "hdfs://192.168.1.50:9000/user/liaohong/"
    
        pass
    #根据产品线配置  批量混合各个算法策略
    def abtest_gen_rsonglist(self,pt):
        if pt not in self.product.keys():
            logging.warning("product name not valid")
            return 0
        my_modeldict = self.parse_config()
        strategy = self.product[pt]["strategy"]
        pt_key = self.product[pt]["key"]
        pt_class = self.product[pt]["class"]
        weight_total = 0
        res = {}
        if pt_class == "song":
            pt_rdd = self.song_dict 
        elif pt_class == "album":
            pt_rdd = self.album_dict 
        elif pt_class == "singer":
            pt_rdd = self.singer_dict 
        else:
            logging.fatal("product strategy class is not valid , please check file base_config.py , pt_class is [%s]"%(pt_class))
            return False

        #创建空的rdd，用于合并策略中的所有rdd
        Trdd = self.sc.parallelize([])
        
        for item in strategy:
            model_info = my_modeldict[str(item["modelid"])]
            key = model_info["key"]
            weight = item["weight"]
            weight_total += weight
            if re.search("songid$",key):
                pre = re.search(".*(?=songid$)",key).group()
                key_rdd = pt_rdd.map(lambda word: (word , get_redis(pre,word)) ).map(lambda a : add_pre(a[0],a[1] * weight)) #乘以权重
                #合并所有策略得到的rdd
                Trdd = Trdd.union(key_rdd)
        
        #所有结果合并，根据key合并所有value(加和，add ，上一步已经添加权重)
        Trdd = Trdd.flatMap(lambda a : a).reduceByKey(add).map(lambda x: (x[0],x[1] / weight_total)).sortBy(lambda x: x[1])
       
        key_tail = pt_key.split("_")[-1]
        key_pre = pt_key.replace(key_tail,"")
        Trdd = Trdd.map(lambda a: (key_pre + a[0].split("_")[0] ,(a[0].split("_")[1] , a[1]) )).groupByKey().mapValues(list)
        
        #统一保存到hdfs上
        path = self.hdfs_pre + "%s/%s"%(pt,datetime.datetime.now().strftime("%Y%m%d"))
        
        self.save_res(Trdd,path)
        
        #灌入redis
        self.import_redis(path,pt)
        pass 
   
    def get_redis(self,multi_type,key):
        if multi_type == "zset":
            return self.redis.zrange(key,0,-1,withscores=True)
        elif multi_type == "string":
            return self.redis.get(key)

    #处理zset类型
    def proc_zset(self,item):
        if not isinstance(item,list):
            logging.WARNING("zset data is not valid, please check!")
        res = []
        print(item)
            
    #返回RDD
    def load_dict(self,dict_type):
        if dict_type == "song":
            return self.sc.textFile(song_dict_path)
        if dict_type == "album":
            return self.sc.textFile(album_dict_path)
        if dict_type == "singer":
            return self.sc.textFile(singer_dict_path)

        pass

    #应注意权限问题，需要删除文件路径
    def save_res(self,final_rdd,path):
        #hdfs路径
        if re.search("hdfs",path):
            #先创建，再删除最底层目录下文件
            mkdir_cmd = "hadoop fs -mkdir -p %s"%(path)
            if subprocess.getstatusoutput(mkdir_cmd)[0] != 0:
                logging.fatal("create hdfs path failed , please check the hdfs path: [%s]"%(path))
                return False

            #需要删除当日时间目录(而不仅仅是文件)
            del_cmd = "hadoop fs -rmr -f %s"%(path)
            if subprocess.getstatusoutput(del_cmd)[0] != 0:
                logging.warning("del path failed , please check the hdfs path: [%s]"%(path))
            else:
                final_rdd.saveAsTextFile(path)
        else:
            #先创建，再删除最底层目录下文件
            os.makedirs(path)

            del_cmd = "rm -rf %s"%(path)
            if subprocess.getstatusoutput(del_cmd)[0] != 0:
                logging.warning("del path failed , please check the local path: [%s]"%(path))
            else:
                final_rdd.saveAsTextFile(path)
        pass

    #暂时使用本地方式导入redis
    def import_redis(self,path,pt):
        if re.search("hdfs",path):
            #先获取到本地
            local_file = "%s/%s/%s/"%(self.DATA_DIR,pt,datetime.datetime.now().strftime("%Y%m%d"))
            if not os.path.exists(local_file):
                os.makedirs(local_file)

            local_filename = local_file+"result"

            get_cmd = "hadoop fs -getmerge %s %s"%(path,local_filename)

            if subprocess.getstatusoutput(get_cmd)[0] == 0:
                data = self.load_res(local_filename)
                r = redis.Redis(host=redis_ip, port=redis_port, db=0)
                for k,v in data.items():
                    #结果大于0个时，再删除原key
                    if len(v) > 0:
                        self.redis.delete(k)
                    try:
                        for tmp in v:
                            count = 0
                            #权重大于0的关联歌曲才放到redis中去
                            if float(tmp[1]) > 0:
                                count += 1
                                if count == SINGLE_KEY_MAX:
                                    break
                                r.zadd(k ,{tmp[0]: tmp[1]})
                        self.redis.expire(k, EXPIRE_TIME)
                    except Exception as e:
                        logging.warning("some thing is wrong while import redis , problem is: [%s]"%(e))
            else:
                logging.warning("from hdfs get data failed , please check the hdfs path: [%s]"%(path))
        else:
            
            pass
        pass 

    def load_res(self,local_path):
        res = {}
        for line in open(local_path, "r"):
            line = line.strip()
            items = eval(line)
            key = items[0]
            v_list = sorted(items[1],key=lambda d: d[1], reverse=True)
            res[key] = v_list
        return res
        pass 

    def parse_config(self):
        model_dict = {}
        for i in all_model:
            model_id = str(i["id"])
            model_dict[model_id] = i
        return model_dict
        pass 

def run():
    #串行执行(todo : 提供选择并行或串行)
    for k,v in product_strategy.items():
        logging.info("begin process product : [%s]."%(k))
        AB = ABTest().abtest_gen_rsonglist(k)
        logging.info("end process product : [%s]."%(k))
        

if __name__ == "__main__":
    #AB = ABTest().abtest_gen_rsonglist("linear_similar_song")
    
    run()

    pass
