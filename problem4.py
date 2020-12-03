#平均応答時間を求めるときのハイフンの扱い
#dataframeの行数がm以上なら...を追加
#直近m回のうちどれを過負荷状態の開始/終了とするか
#過負荷状態が終わっていないときに出力されない問題
import datetime
import math
import pandas as pd

f = open('monitoring.log', 'r')

datalist = f.readlines()
time_ip_ping = []
#故障しているサーバを一時的に記録
trouble = []
#故障したサーバを記録
trouble_record = []
#故障候補のサーバを記録
trouble_candidate = []
#ログに記録しているサーバのリスト
ip_list = []
#ネットワークとIPアドレスの対応表
ip_subnet_list = []
#平均応答時間のリスト
responsetime_list = []
#ネットワークのリスト、故障情報も含む
subnet_failure = []

#タイムアウト回数
N = 3
#直近m回の平均応答時間tミリ秒
m = 2
t = 30

#時刻,IP,応答時間に分ける
for data in datalist:
    data = data.strip('\n')
    time_ip_ping.append(data.split(',')); 

df_time_ip_ping = pd.DataFrame(time_ip_ping)
df_time_ip_ping.columns = ['time', 'ip', 'ping']

#サーバのリストを作成
for data in time_ip_ping:
    if not data[1] in ip_list:
        ip_list.append(data[1])

#IPアドレスを2進数に変換
for ip in ip_list:
    ip_split, subnet_temp = ip.split('/')
    ip_split = ip_split.split('.')
    ip_bin = ""
    subnet = ""
    for item in range(int(subnet_temp)):
        subnet = subnet+"1"
    subnet = subnet.ljust(32, '0')
    for item in ip_split:
        ip_bin = ip_bin+format(int(item),'08b')
    #IPアドレスとネットワークの対応表を作成
    ip_subnet_list.append({ip:bin(int(ip_bin,2)&int(subnet,2)), "failure":0})
    #ネットワークのリストを作成
    network_existence_flag = 0
    for item in subnet_failure:
        if item.get("network") == bin(int(ip_bin,2)&int(subnet,2)):
            network_existence_flag = 1
    if network_existence_flag == 0:
        subnet_failure.append({"network":bin(int(ip_bin,2)&int(subnet,2)), "time":"", 'failure_flag':0, "timeout":0})

#ログを行ごとに調べる
for data in time_ip_ping:
    #すでに故障しているサーバがあれば
    if trouble:
        for index, trouble_data in enumerate(trouble):
            #故障しているサーバとIPが一致しているか
            if trouble_data[1] == data[1]:
                #ping応答が返ってくるようになっていれば故障期間を出力
                if data[2] != '-':
                    start_failure = datetime.datetime.strptime(trouble_data[0], '%Y%m%d%H%M%S')
                    end_failure = datetime.datetime.strptime(data[0], '%Y%m%d%H%M%S')
                    print("failure time:", end_failure-start_failure, ", IP address:", data[1], ', start:', start_failure, ', end:', end_failure)
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
                    #ネットワークIP対応表のタイムアウト回数を更新
                    #for item in ip_subnet_list:
                    #    if data[1] in item:
                    #        item["timeout"] += 1
                    #        print(data[1], item["timeout"])

                    #規定回数タイムアウトしていたら故障リストに追加、候補から削除
                    if trouble_candidate_data[3] >= N:
                        trouble.append(trouble_candidate_data)
                        del trouble_candidate[index]

            #新たな故障候補だった場合、タイムアウト回数(1)をデータに加えて候補リストに追加
            if trouble_candidate_flag == 0:
                data.append(1)
                trouble_candidate.append(data)
                #ネットワークIP対応表のタイムアウト回数を1に更新
                #for item in ip_subnet_list:
                #    if data[1] in item:
                #        item["timeout"] = 1
        
        #ネットワーク内のタイムアウト回数を更新したい
        for ip_subnet_data in ip_subnet_list:
            if data[1] in ip_subnet_data:
                ip_subnet_data["failure"] = 1
                for subnet_failure_data in subnet_failure:
                    if subnet_failure_data["network"] == ip_subnet_data[data[1]]:
                        #ネットワーク内で初めてのタイムアウトなら時刻を記録
                        if subnet_failure_data["timeout"] == 0:
                            subnet_failure_data["time"] += data[0]
                        #タイムアウト回数を更新
                        subnet_failure_data["timeout"] += 1

        #ネットワーク内でN回タイムアウトかつ全てのサーバでタイムアウトありならば
        for subnet_failure_data in subnet_failure:
            #タイムアウトしていないサーバがあるかチェック
            safe_flag = 0
            if subnet_failure_data['timeout']>=N:
                for ip_subnet_data in ip_subnet_list:
                    for ip_data in ip_list:
                        if ip_data in ip_subnet_data:
                            if ip_subnet_data[ip_data] == subnet_failure_data["network"]:
                                if ip_subnet_data["failure"] == 0:
                                    safe_flag = 1
                if safe_flag == 0:
                    subnet_failure_data["failure_flag"] = 1
                    print("subnet failure:",subnet_failure_data["network"], "start:", subnet_failure_data["time"])
    #タイムアウトしていないとき
    else:
        #ネットワーク内のタイムアウト回数を0に更新したい
        for ip_subnet_data in ip_subnet_list:
            if data[1] in ip_subnet_data:
                ip_subnet_data["failure"] = 0
                for subnet_failure_data in subnet_failure:
                    if subnet_failure_data["network"] == ip_subnet_data[data[1]]:
                        #ネットワーク内で故障中だったら故障期間を出力して削除
                        if subnet_failure_data["failure_flag"] == 1:
                            subnet_failure_data["failure_flag"] = 0
                            print("subnet failure:",subnet_failure_data["network"], "start:", subnet_failure_data["time"])
                        subnet_failure_data["timeout"] = 0
                        subnet_failure_data["time"] = ""
                        
                        
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
            #print(overload_data)
        #過負荷状態が解消されていたら過負荷状態期間を出力
        elif overload_flag == 1 and math.ceil(responsetime) <= t:
            overload_flag = 0
            start_overload = datetime.datetime.strptime(overload_data.loc[0, "time"], '%Y%m%d%H%M%S')
            end_overload = datetime.datetime.strptime(responsetime_data["time"][index], '%Y%m%d%H%M%S')
            print("overload condition time:", end_overload-start_overload, ",ip address:",responsetime_data["ip"][0], "start:", start_overload, "end:", end_overload)

f.close()