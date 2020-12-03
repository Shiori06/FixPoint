import datetime
import sys
import math
import pandas as pd

args = sys .argv

f = open('monitoring.log', 'r')

datalist = f.readlines()
time_ip_ping = []
#故障しているサーバを記録
trouble = []
#故障候補のサーバを記録
trouble_candidate = []
#ログに記録しているサーバのリスト
ip_list = []
#平均応答時間のリスト
responsetime_list = []

#タイムアウト回数
N = 3
#直近m回の平均応答時間tミリ秒
m = 2
t = 30

if len(args)>1:
    N = int(args[1])
if len(args)>3:
    m = int(args[2])
    t = int(args[3])

#時刻,IP,応答時間に分ける
for data in datalist:
    data = data.strip('\n')
    time_ip_ping.append(data.split(',')); 

df_time_ip_ping = pd.DataFrame(time_ip_ping)
df_time_ip_ping.columns = ['time', 'ip', 'ping']

#ログを行ごとに調べる
for data in time_ip_ping:
    #サーバのリストを作成
    if not data[1] in ip_list:
        ip_list.append(data[1])

    #すでに故障しているサーバがあれば
    if trouble:
        for index, trouble_data in enumerate(trouble):
            #故障しているサーバとIPが一致しているか
            if trouble_data[1] == data[1]:
                #ping応答が返ってくるようになっていれば故障期間を出力
                if data[2] != '-':
                    start_failure = datetime.datetime.strptime(trouble_data[0], '%Y%m%d%H%M%S')
                    end_failure = datetime.datetime.strptime(data[0], '%Y%m%d%H%M%S')
                    print("failure time:", end_failure-start_failure, " IP address:", data[1], ', start:', start_failure, ', end:', end_failure)
                    del trouble[index]

    #すでに故障候補のサーバが1つでもあれば
    if trouble_candidate:
        for index, trouble_candidate_data in enumerate(trouble_candidate):
            #故障候補のサーバとIPが一致しているか
            if trouble_candidate_data[1] == data[1]:
                #ping応答が返ってくるようになっていれば故障候補から除外
                if data[2] != '-':
                    del trouble_candidate[index]

    #タイムアウトの検知
    if data[2] == '-':
        #発見されたタイムアウトがすでに故障しているサーバかチェック
        trouble_flag = 0
        for trouble_data in trouble:
            if trouble_data[1] == data[1]:
                trouble_flag = 1

        #新たに発見されたタイムアウトだった場合
        if trouble_flag == 0:
            #故障候補に入っているかチェック
            trouble_candidate_flag = 0
            for index, trouble_candidate_data in enumerate(trouble_candidate):
                #候補に入っていればタイムアウト回数を更新
                if trouble_candidate_data[1] == data[1]:
                    trouble_candidate_flag = 1
                    trouble_candidate_data[3] = trouble_candidate_data[3]+1
                    #規定回数タイムアウトしていたら故障リストに追加、候補から削除
                    if trouble_candidate_data[3] >= N:
                        trouble.append(trouble_candidate_data)
                        del trouble_candidate[index]

            #新たな故障候補だった場合、タイムアウト回数(1)をデータに加えて候補リストに追加
            if trouble_candidate_flag == 0:
                data.append(1)
                trouble_candidate.append(data)

#タイムアウトしている行を削除
drop_index = df_time_ip_ping.index[df_time_ip_ping['ping']=='-']
df_ping = df_time_ip_ping.drop(drop_index)
#ipアドレスごとにdataframeにして配列にする
for ip in ip_list:
    responsetime_list.append(df_ping.query('ip == "'+ip+'"').reset_index(drop=True))

#ipアドレスごとに平均応答時間を計算
for responsetime_data in responsetime_list:
    #すでに過負荷状態であるかのチェック用
    overload_flag = 0
    #一つのipアドレス内でチェック
    for index in range(len(responsetime_data)-m+1):
        #応答時間の合計
        sum = 0
        for num in range(m):
            sum += int(responsetime_data["ping"][index+num])
        #平均応答時間
        responsetime = sum/m

        #過負荷状態でなく、tミリ秒を超えたら過負荷状態開始として記録
        if overload_flag == 0 and math.ceil(responsetime) > t:
            overload_flag = 1
            overload_data = responsetime_data[index:index+1].reset_index(drop=True)
        #過負荷状態が解消されていたら過負荷状態期間を出力
        elif overload_flag == 1 and math.ceil(responsetime) <= t:
            overload_flag = 0
            start_overload = datetime.datetime.strptime(overload_data.loc[0, "time"], '%Y%m%d%H%M%S')
            end_overload = datetime.datetime.strptime(responsetime_data["time"][index], '%Y%m%d%H%M%S')
            print("overload condition time:", end_overload-start_overload, ", IP adress:", responsetime_data["ip"][0], ", start:", start_overload, ", end:", end_overload)

f.close()