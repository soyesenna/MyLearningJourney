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

