import time
b = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
a = input('[1.十转二 2.十转八 3.十转十六][4.二转十 5.八转十 6.十六转十]>>>')
if a == '1' or a == '2' or a == '3' or a == '4' or a == '5' or a == '6':
    if a == '1':
        c = input('请输入一个十进制数>>>')
        for i in c:
            if i in b:
                print('结果是' + bin(int(c))[2:])
                break
            else:
                print('只能输入数字哦')
                break
    elif a == '2':
        c = input('请输入一个十进制数>>>')
        for i in c:
            if i in b:
                print('结果是' + oct(int(c))[2:])
                break
            else:
                print('只能输入数字哦')
                break
    elif a == '3':
        c = input('请输入一个十进制数>>>')
        for i in c:
            if i in b:
                print('结果是' + hex(int(c))[2:])
                break
            else:
                print('只能输入数字哦')
                break
    elif a == '4':
        c = input('请输入一个二进制数>>>')
        for i in c:
            if i in b:
                print('结果是' + str(int(c, 2)))
                break
            else:
                print('只能输入数字哦')
                break
    elif a == '5':
        c = input('请输入一个八进制数>>>')
        for i in c:
            if i in b:
                print('结果是' + str(int(c, 8)))
                break
            else:
                print('只能输入数字哦')
                break
    elif a == '6':
        c = input('请输入一个十六进制数>>>')
        for i in c:
            print('结果是' + str(int(c, 16)))
            break
else:
    print('只能输入1/2/3/4/5/6哦')
print('5秒后自动关闭程序')
time.sleep(5)
