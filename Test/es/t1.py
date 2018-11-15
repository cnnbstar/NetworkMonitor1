#!/usr/bin/env python27
# -*- coding: utf-8 -*-

import os
import time
from os import walk
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import sys

es_hosts = ["10.15.6.4"]
index_name = "syslog-2018.09"
doc_type = "syslog"
xx_id = "AWYjDRWGaaOT0gr4krT8"
es = Elasticsearch(['10.15.6.4'],port=9200)


def main():
    # es.indices.create(index=index_name,
    #                   body={"mappings":{"_score": {"_source":{"message":"text"}}}})
    res = es.search(index=index_name,
                    doc_type=doc_type,
                    body={"query": {"match_all": {}}})
    print(res)

def es_search(host):
    #获取全部
    my_body_all = {
        "query":{
            "match_all":{}
        }
    }

    #匹配host=10.15.253.251
    my_body = {
        "query":{
            "term":{
                "host":"10.15.253.251"
            }
        }
    }

    #匹配host=10.15.30.30&10.15.253.251
    my_body2 = {
        "query":{
            "terms":{
                "host":["10.15.30.30","10.15.253.251"]
            }
        }
    }

    #匹配host包含10.15.30.30
    my_body3 = {
        "query":{
            "match":{
                "host":"10.15.253.251"
            }
        },
        "_source":["host","message"],
        "from":2,#从第二条数据开始
        "size":1 #获取4条数据
    }

    #复合查询bool
    #bool有三类查询关系，must（都满足），should（其中一个满足），must_not(都不满足)
    my_body4 = {
        "query":{
            "bool":{
                "must":[
                    { "term":{"name":"hello"} },
                    { "term":{"age":18} }
                ],
                "must_not":[
                    {"term":{"name":"xx"}}
                ],
                "should":[
                    {"term":{"name":"yy"}}
                ]
            }
        }
    }

    source_arr = [
        "host","message"
    ]

    res = es.search(index=index_name,body=my_body3)

    return res






if __name__ == '__main__':
    #main()
    print  os.environ.get('SECRET_KEY') or '2vym+ky!997d5kkcc64mnz06y1mmui3lut#(^wd=%s_qj$1%x'

    print es_search("10.15.253.251")
