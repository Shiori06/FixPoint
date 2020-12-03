#最後の改行文字たちを消したい
import datetime

f = open('monitoring.log', 'r')

datalist = f.readlines()
time_ip_ping = []
trouble = []

#時刻,IP,応答時間に分ける
for data in datalist:
    data = data.strip('\n')
    time_ip_ping.append(data.split(',')); 

#ログを行ごとに調べる
for data in time_ip_ping:
    #すでに故障しているサーバがあれば
    if trouble:
        for index, trouble_data in enumerate(trouble):
            #故障しているサーバとIPが一致しているか
            if trouble_data[1] == data[1]:
                #ping応答が返ってくるようになっていれば故障期間を出力、リストから削除
                if data[2] != '-':
                    start_failure = datetime.datetime.strptime(trouble_data[0], '%Y%m%d%H%M%S')
                    end_failure = datetime.datetime.strptime(data[0], '%Y%m%d%H%M%S')
                    print("failure time:", end_failure-start_failure, ", IP address:", data[1],  ', start:', start_failure, ', end:', end_failure)
                    del trouble[index]

    #タイムアウトの検知
    if data[2] == '-':
        #発見されたタイムアウトがすでに故障しているサーバかチェック
        trouble_flag = 0
        for trouble_data in trouble:
            if trouble_data[1] == data[1]:
                trouble_flag = 1

        #新たに発見された故障だった場合、リストに追加
        if trouble_flag == 0:
            trouble.append(data)

f.close()