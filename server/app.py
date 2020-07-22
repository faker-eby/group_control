

import json
import hashlib
from flask import Flask,request
import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='q2251682', db='bixin', charset='utf8mb4')
app = Flask(__name__)
@app.route("/uploadInfo", methods=["POST"])
def receiveInfo():
    if request.method == 'POST':
        receive_data = request.get_data()
        receive_json = json.loads(receive_data)
        if checkSign(receive_json["data"],receive_json["sign"])!=0:
            insert_result = insertData(receive_json["data"])
            if insert_result!=0:
                return {"code":100,"msg":str(insert_result)}
            else:
                return {"code":0,"msg":"SUCCESS"}
        else:
            return "非法请求"
    else:
        return '<h1>只接受post请求！</h1>'
#对sign进行检验
def checkSign(data,sign):
    md5_data = md5(data)
    local_sign = algorithmSign(md5_data)
    if local_sign==sign:
        return 0
    else:
        return local_sign
#对传入md5加密
def md5(string):
    strings = hashlib.md5()
    strings.update(str(string).encode("utf8"))
    return strings.hexdigest()
#sign的进一步算法
def algorithmSign(sign):
    sign = sign.replace('a','c')
    sign = sign.replace('6','8')
    sign = sign.replace('f','z')
    sign = sign.replace('e','a')
    sign = sign.replace('3','6')
    sign = sign.replace('1','3')
    sign = sign.replace('5','7')
    sign = sign.replace('8','9')
    return sign
#向数据库插入接收到的信息
def insertData(data):
    try:
        ###############插入前先检查数据库是否存在################
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute("select nickname from id_info where nickname='%s'and belong_key='%s'" %(data["nickname"],data["belong_key"]))
        query_nickname = cursor.fetchone()
        cursor.close()
        ########################################################
        if query_nickname:   
            return "目标已存在"
        else:
            cursor = conn.cursor()#创建游标
            cursor.execute("INSERT INTO id_info (nickname,gender,belong_key,insert_time) values ('%s','%s','%s',NOW())" %(data["nickname"],data["gender"],data["belong_key"]))
            conn.commit()
    except Exception as err:
        return err
    finally:
        cursor.close()
    print("插入成功")
    return 0
#插入工作室信息
def room_insertData(data):
    try:
        ###############插入前先检查数据库是否存在################
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute("select nickname from room_id_info where nickname='%s'and belong_key='%s'" %(data["nickname"],data["belong_key"]))
        query_nickname = cursor.fetchone()
        cursor.close()
        ########################################################
        if query_nickname:   
            return "目标已存在"
        else:
            cursor = conn.cursor()#创建游标
            cursor.execute("INSERT INTO room_id_info (nickname,gender,game,insert_time,use_times,belong_key) values ('%s','%s','%s',NOW(),0,'%s')" %(data["nickname"],data["gender"],data["game"],data["belong_key"]))
            conn.commit()
    except Exception as err:
        return err
    finally:
        cursor.close()
    return 0
#生成md5
@app.route("/getMd5", methods=["POST"])
def getMD5():
     if request.method == 'POST':
        receive_data = request.get_data()
        receive_json = json.loads(receive_data)
        return md5(receive_json)
@app.route("/query/<uuid>", methods=["get"])
def out_data(uuid):
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute("select belong_key from admin_key where uuid='%s'" %uuid)
    query_key = cursor.fetchone()
    cursor.close()
    if query_key:
        local_belong_key = query_key["belong_key"]
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute("select * from id_info where belong_key='%s'" %local_belong_key)
        query_key = cursor.fetchone()
    else:
        return "无效key，拒绝访问"
@app.route("/room/query", methods=["post"])
def room_query():
    if request.method == 'POST':
        receive_data = request.get_data()
        receive_json = json.loads(receive_data)
        uuid = receive_json["uuid"]
        key = room_admin_check(uuid)
        if key:
            return room_query_data(key["belong_key"],receive_json)
        else:
            return "无效key,禁止访问"
    else:
        return '<h1>只接受post请求！</h1>'
@app.route("/room/uploadInfo", methods=["POST"])
def room_updateInfo():
    if request.method == 'POST':
        receive_data = request.get_data()
        receive_json = json.loads(receive_data)
        if checkSign(receive_json["data"],receive_json["sign"])!=0:
            insert_result = room_insertData(receive_json["data"])
            if insert_result!=0:
                return {"code":100,"msg":str(insert_result)}
            else:
                return {"code":0,"msg":"SUCCESS"}
        else:
            return {"code":400,"msg":"非法请求"}
    else:
        return '<h1>只接受post请求！</h1>'
#查找工作室uuid对应的key
def room_admin_check(uuid):
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute("select belong_key from room_admin_key where uuid='%s'" %uuid)
    query_key = cursor.fetchone()
    if(query_key):
        return query_key
    else:
        return False
#查找工作室id_info数据
def room_query_data(belong_key,data):
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    if(data["gender_filter"] and data["game_filter"]):
        print("性别及技能都进行了筛选")
        cursor.execute("select * from room_id_info where belong_key='%s' and instr('%s',game) and gender='%s' order by use_times,insert_time desc" %(belong_key,data["game_filter"],data["gender_filter"]))
    elif(data["gender_filter"]): 
        print("性别进行了筛选")
        cursor.execute("select * from room_id_info where belong_key='%s' and gender='%s' order by use_times,insert_time desc" %(belong_key,data["gender_filter"]))
    elif(data["game_filter"]):
        print("技能进行了筛选")
        cursor.execute("select * from room_id_info where belong_key='%s' and instr('%s',game) order by use_times,insert_time desc" %(belong_key,data["game_filter"]))
    else:
        print("不筛选")
        cursor.execute("select * from room_id_info where belong_key='%s' order by use_times,insert_time desc" %belong_key)
    query_data = cursor.fetchone()
    cursor.close()
    if(query_data):
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute("UPDATE room_id_info set use_times= IFNULL(use_times,0)+1 WHERE nickname='%s' and belong_key='%s'"%(query_data["nickname"],belong_key))
        conn.commit()
        cursor.close()
        return {"code":0,"msg":"SUCCESS","data":query_data}
    else:
        return {"code":-100,"msg":"无符合要求的用户"}
app.run(debug=True,host="0.0.0.0",port="6050")