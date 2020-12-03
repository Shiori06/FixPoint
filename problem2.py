#パラメータで与えられるようにする
import datetime

f = open('monitoring.log', 'r')

datalist = f.readlines()
time_ip_ping = []
trouble = []
trouble_candidate = []


N = 3

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
                #ping応答が返ってくるようになっていれば故障期間を出力
                if data[2] != '-':
                    start_failure = datetime.datetime.strptime(trouble_data[0], '%Y%m%d%H%M%S')
                    end_failure = datetime.datetime.strptime(data[0], '%Y%m%d%H%M%S')
                    print("IP address:", data[1], ", failure time:", end_failure-start_failure, ', start:', start_failure, ', end:', end_failure)
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

f.close()