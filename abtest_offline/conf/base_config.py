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

product_strategy = {
    "linear_similar_song":{
        "name":"linear_similar_song",
        "class":"song",                     #使用哪种类型的rdd(song，album，singer)，基础数据
        "key":"abtest_simSong_songid",      #合并策略灌入redis 的结果key
        "source":23,
        "rerankid":2,
        "strategy":[                        #策略  混合多种model
            {
                "modelid":18,
                "weight":2
            },
            {
                "modelid":19,
                "weight":2
            }
        ]
    },
    "linear_similar_song_2":{
        "name":"linear_similar_song_2",
        "class":"song",                     #使用哪种类型的rdd(song，album，singer)，基础数据
        "key":"abtest_simSong_2_songid",    #合并策略灌入redis 的结果key
        "source":24,
        "rerankid":2,
        "strategy":[                        #策略  混合多种model
            {
                "modelid":19,
                "weight":2
            },
            {
                "modelid":20,
                "weight":2
            }
        ]
    },
        
}

#abtest分流
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





