#!/usr/bin/env python3
# -*- coding:utf-8 -*-

DEFAULT_WEIGHT = 1 #每个关联算法默认比重

#基础库地址
#song_dict_path="ftp://192.168.5.215:/home/work/odp/webroot/downloads/quku/song.id.dat"
song_dict_path="song.id.dat"

album_dict_path="album_dict"

singer_dict_path="singer_dict"

#基础算法模型  strategy 混合使用
all_model=[
    {
        "id":18,
        "name":"cf_new",
        "version":"1.0.0",
        "source":"1",
        "struct":"zset",
        "key":"cf_songnw_songid"
    },
    {
        "id":19,
        "name":"lrc_simiSong",
        "version":"1.0.0",
        "source":"1",
        "struct":"zset",
        "key":"lrc_simiSong_songid"
    },
    {
        "id":20,
        "name":"list_arm",
        "version":"1.0.0",
        "source":"1",
        "struct":"zset",
        "key":"baidulist_arm_songid"
    }
]

all_rerank=[
    {
        "id":1,
        "name":"old_rerank",
        "version":"1.0.0"
    },
    {
        "id":2,
        "name":"usermodel_rerank",
        "version":"1.0.0"
    }
]

product = {
    "linear_similar_song":{
        "name":"linear_similar_song",
        #使用哪种类型的rdd(song，album，singer)，基础数据
        "class":"song",
        #合并策略灌入redis 的结果key
        "key":"abtest_simSong_songid",
        "source":23,
        "rerankid":2,
        #策略  混合多种model
        "strategy":[
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
        
}






