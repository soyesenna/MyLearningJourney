# 삽질 저장소 입니다.

* 2021.10.17

  * #### `Git과 Github간단 사용법`

  * Git Repository 생성하고 컴퓨터 내 Directory와 연결

    * github들어가서 new repository로 생성

    * 연결하고 싶은 directory에서 git bash 실행
  
    * 1. git init
      2. git remote add origin "내 주소"

      위의 순서대로하면 github과 내 directory가 연결됨\

  * Directory를 github에 올리기
  
    * 1. git add . (.은 현재 directory, 다른 경로 지정도 됨)
      2. git commit -m "메시지(설명)"
      3. git push origin master

      위의 순서대로 하면 add로 지정한 디렉토리 내의 파일들이 github으로 올라감(push됨)

  * add, commit, push, status, log, clone
  
    * add : staging 하기위한 커맨드.
    * commit : staging된 directory를 저장?하는 커맨드.
    * push : commit된 것들을 github으로 올리는 커맨드.
    * status : 현재 상태를 보여주는듯
    * log : 이전 commit한 기록을 보여줌.
    * clone : 다른 github에서 통째로 복사하는 것.
  
* 2021.10.18

  * #### `파이썬 엑셀 라이브러리 openxlpy 간단 사용법`

  * 엑셀 워크북 변수 생성(전체적인 엑셀 파일의 정보를 담고있다)

    * wb = openpyxl.Workbook()

  * 생성한 워크북의 시트 불러오기

    * ws = wb.active >> 현재 활성중인 시트를 불러오는것
    * ws = wb['sheet2'] >>시트의 이름으로 불러오는것

  * 새로운 시트 만들기

    * wb.create_sheet(title='new_sheet') >> wb는 워크북변수

  * 셀의 크기 바꾸기

    * ws.colum_dimensions['A'].width = 1 >> ws는 워크시트변수, A열의 너비를 바꾼다
    * ws.row_dimensions['1'].height = 1 >> 1행의 높이를 바꾼다
      * 이때 워크시트 변수를 바꾸면 다른 워크시트에 적용 가능

  * openpyxl의 이미지 불러오기

    * img = openpyxl.drawing.image.Image('이미지 경로')

  * openpyxl의 이미지크기 조절하기

    * img.height = 1
    * img.width = 1
      * img는 불러온 이미지의 정보를 담고있는 변수

  * 셀에 값 입력하기

    * ws['A1'] = '입력할 값'
      * ws는 워크시트 변수, 대괄호안에는 열행의 순서로 셀의 좌표를 입력한다

  * 셀에 이미지 넣기

    * ws.add_image(img, 'A1')
      * ws는 워크시트 변수, img는 불러온 이미지의 정보를 담고있는 변수

  * 엑셀 파일 저장하기

    * wb.save('저장할 경로')
      * wb는 워크북 변수

