---
tistoryBlogName: soyesenna
tistoryTitle: (혼자 공부하는 SQL) Chapter 1
tistoryVisibility: "3"
tistoryCategory: "1150625"
tistorySkipModal: true
tistoryPostId: "3"
tistoryPostUrl: https://soyesenna.tistory.com/3
---
--- 
## 1-1 데이터 베이스 알아보기
- 데이터베이스는 ***데이터의 집합*** 이라고 할 수 있다

#### 데이터베이스와 DBMS
- 데이터베이스를 ***데이터의 집합***이라고 정의한다면, 이런 데이터베이스를 관리하고 운영하는 소프트웨어를 DBMS(Database Management System)라고 한다
- 다양한 데이터가 저장되어 있는 데이터베이스는 여러 명의 사용자나 응용프로그램과 공유하고 동시에 접근이 가능해야 한다
	- 하지만 예전에 파일로 데이터를 관리할 떄는 많은 데이터를 처리하기 어려웠고, 여러 사용자가 동시에 작업할 수 없었다
	- 즉, DBMS는 대량의 데이터를 효율적으로 관리하고 운영하기 위해서 등장한 것
- DBMS에 데이터를 구축, 관리하고 활용하기 위해서 사용되는 언어가 SQL(Structured Query Language)

#### DBMS의 분류
- DBMS의 유형은 계층형(Hierarchical), 망형(Network), 관계형(Relational), 객체지향형(Object-Oriented), 객체관계형(Object-Relational) 이 있다
- 현재 가장 많이 사용되는 DBMS는 RDBMS(관계형)이다

- 계층형 DBMS
	- 계층형 DBMS는 처음으로 등장한 DBMS개념이다
	- 데이터들의 계층은 트리 형태를 가진다
	- 계층형의 문제는 처음 구성을 완료한 후에 이를 변경하기가 상당히 까다롭다는 것과 다른 구성원을 찾아가는 것이 비효율적이라는 것
	- 지금은 사용하지 않음
- 망형 DBMS
	- 망형 DBMS는 계층형 DBMS의 문제점을 개선하기 위해 등장
	- 망형은 하위에 있는 구성원끼리도 연결된 유연한 구조
	- 하지만 망형을 잘 활용하려면 프로그래머가 모든 구조를 이해해야만 프로그램 작성이 가능하다는 것
	- 지금은 사용하지 않음
- 관계형 DBMS
	- 관계형 DBMS(RDBMS)는 테이블이라는 최소 단위로 구성되며, 이 테이블은 하나 이상의 열과 행으로 이루어져 있다
	- RDBMS에서는 모든 데이터가 테이블에 저장된다
		- 테이블은 열과 행으로 이루어진 2차원 구조를 가진다(세로 : 열, 가로 : 행)
	- 현재 가장 많이 사용되고 있는 형태

#### DBMS에서 사용되는 언어: SQL
- SQL은 관계형 데이터베이스에서 사용되는 언어
- 국제 표준인 표준 SQL이 있지만 표준SQL만으로는 DBMS를 만드는 회사들의 특성을 모두 포용하지 못한다
	- 따라서 각 회사는 표준 SQL을 되도록 준수하되, 각 제품의 특성을 반영한 SQL을 사용한다

--- 
## 1-2 MySQL설치하기

### ***설치 완료***

--- 

