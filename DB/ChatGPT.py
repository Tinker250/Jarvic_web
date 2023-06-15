import pymysql
import uuid
import re

db_host = os.getenv("DB_HOST")
db_psw = os.getenv("DB_PSW")

class GPTProcessor():
    def __init__(self):
        self.conn = pymysql.connect(host=db_host,port=3306,user='root',password=db_psw,db='Jarvic',charset="utf8")
    
    def add_result_row(self,query):
        cursor = self.conn.cursor()
        request_id = str(uuid.uuid1())
        request_id = re.sub('-','',request_id)
        #VALUE第三个元素使这个请求的处理状态 0-创建了正在post 1-完成post结果写入 2-error
        insert_sql = 'INSERT INTO ChatGPT_Request VALUES (%s, %s, %s,%s)'
        cursor.execute(insert_sql,(request_id,"",0, query))
        #检查sql执行结果，正常则不用额外处理
        rows = cursor.fetchone()
        # 关闭游标
        self.conn.commit()
        cursor.close()
        return request_id

    def update_record_to_mysql(self,request_id,text):
        cursor = self.conn.cursor()
        #VALUE第三个元素使这个请求的处理状态 0-创建了正在post 1-完成post结果写入 2-error
        update_sql = 'UPDATE ChatGPT_Request SET ChatGPTResponse=%s, Status=%s WHERE RequestId = %s'
        cursor.execute(update_sql,(text,1,request_id))
        #检查sql执行结果，正常则不用额外处理
        rows = cursor.fetchall()
        print("UPDATE {} successed".format(request_id))
        # 关闭游标
        self.conn.commit()
        cursor.close()
        return request_id
    
    def get_text_from_request_id(self,request_id):
        cursor = self.conn.cursor()
        select_sql = 'SELECT ChatGPTResponse FROM ChatGPT_Request WHERE RequestId = %s AND Status = %s'
        cursor.execute(select_sql,(request_id,1))
        row = cursor.fetchone()
        if(row):
            return row
        else:
            return False


    def close_db(self):
        self.conn.close()