# 삽질 저장소 입니다.

* 2021.10.17

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