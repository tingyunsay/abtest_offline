#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os,re
from base_config import *
from pyspark import SparkConf, SparkContext
import logging
import redis 
from redis_conf import *

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

def get_redis(key):
    r = redis.Redis(redis_ip, redis_port, db=0)
    r_con = r.zrange(key,0,-1,withscores=True)
    return r_con
    

class ABTest(object):
    def __init__(self):
        self.author = "tingyun"
        self.allmodel = self.parse_config()
        self.allrerank = all_rerank 
        self.product = product 
        #local模式(暂时使用此模式)，集群模式需要搭建hadoop
        self.sc = SparkContext("local","APP_NAME")
        
        #conf = SparkConf().setAppName(APP_NAME).setMaster("spark://127.0.0.1:7077")
        #self.sc = SparkContext(conf=conf)
        #歌词库
        #self.song_dict = "./song.id.dat"
        self.song_dict =  self.load_dict("song")
        #专辑库
        #self.album_dict =  self.load_dict("album")
        #歌手库
        #self.singer_dict =  self.load_dict("singer")
        
        
        self.redis = redis.Redis(redis_ip, redis_port, db=0)


        pass
    #根据产品线配置  批量混合各个算法策略
    def abtest_gen_rsonglist(self,pt):
        if pt not in product.keys():
            logging.warning("product name not valid")
            return 0
        my_modeldict = self.parse_config()
        strategy = product["linear_similar_song"]["strategy"]
        res = {}
        
        for item in strategy:
            model_info = my_modeldict[str(item["modelid"])]
            key = model_info["key"]
            weight = item["weight"]
            if re.search("songid$",key):
                pre = re.search(".*(?=songid$)",key).group()
                key_rdd = self.song_dict.map(lambda word: pre + word )
                res = key_rdd.map(get_redis)#.map(lambda item : self.proc_zset(item))#.reduceByKey(lambda a,b:a + b)
                res.saveAsTextFile("/Users/tingyun/PycharmProjects/Tingyun/svn/abtest_offline/tingyun/")

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

    def save_res(self):

        pass

    def parse_config(self):
        model_dict = {}
        for i in all_model:
            model_id = str(i["id"])
            model_dict[model_id] = i
        return model_dict
        pass 


if __name__ == "__main__":
    AB = ABTest().abtest_gen_rsonglist("linear_similar_song")


    pass
