## 2021.10.28

 - ##### 알고리즘 인터뷰 3장 : 파이썬

 - PEP란?

    -  파이썬의 새로운 기능을 제안하고 커뮤니티의 의견을 수렴하여 파이썬의 디자인 결정을 문서화하는 파이썬의 주요 개발 프로세스.

 - 네이밍 컨벤션

    - 파이썬의 변수나 함수의 이름을 결정하는 방식
    - snake case를 따른다
       - snake case는 각 단어를 _(언더바)로 구분하는 것

- 타입 힌트

  - 파이썬에는 변수의 타입을 정할 수 없지만 명시적으로 알려주는게 가능함

    - 가독성을 높여주고 버그를 줄여주는 역할

  - 하지만 강제  규약이 아니라 명시적으로만 알려주는 것이기 때문에 강제성은 없음

    ```python
    from typing import TyVar
    
    #a는 int형, fn함수의 리턴값은 bool형을 명시
    def fn(a: int) -> bool:
      #하지만 강제성이 없기때문에 밑의 문장도 실행이 된다
      return 'this is not bool'
    
    #하지만 강제성이 없기때문에 밑의 문장도 실행이 된다
    fn('this is not int')
    
    ```

  - mypy라는 모듈을 사용하면 타입 힌트에 오류가 있는지 자동으로 확인해줌

    - pip install mypy
    - mypy a.py

- 리스트 컴프리헨션

  - 기존 리스트를 기반으로 새로운 리스트를 만들어내는 구문

    ```python
    [n * 2 for n in range(1, 10 + 1) if n % 2 == 1]
    #[2, 6, 10, 14, 18]
    ```

  - 너무 복잡하게 사용할 경우 가독성을 떨어뜨릴 수 있으므로 표현식은 2개를 넘지 않아야한다

- 제너레이터

  - 제너레이터란 숫자를 만들어 내는 공장같은 것

  - 임의의 숫자 1억개를 생성하고 활용하는 프로그램은 제너레이터를 사용하지 않으면 1억개의 숫자를 메모리 어딘가에 보관하고 있어야한다. 하지만 제너레이터는 생성 조건만 정해두고 필요할때 생성해서 사용할 수 있으므로 훨씬 메모리가 절약된다

  - yield구문을 사용하여 제너레이터를 리턴할 수 있다

    - yield로 넘어온 제너레이터를 next로 받는다

    ```python
    def get_natural_number():
      n = 0
      while True:
        n += 1
        #yield로 생성된 숫자를 양보(yield)한다
        #이때 함수는 끝나지 않고 계속 실행된다
        yield n
    
    g = get_natural_number()
    for _ in range(100):
      #next로 yield된 제너레이터를 받았다
      print(next(g))
      '''
      >> 1
      >> 2
      >> 3
      ...
      '''
      
    ```

    ```python
    def generater():
      yield 1
      yield 'string'
      yield True
     
    g = generater()
    for _ in range(3):
      print(next(g))
     '''
     >> 1
     >> string
     >> True
     '''
    ```

  - 제너레이터 방식을 사용하는 함수로 range가 대표적이다

- enumerate

  - 여러가지 자료형(list, set, tuple등)을 인덱스를 포함한 enumerate객체로 리턴한다

    ```python
    a = [1,2,3,4,5]
    print(enumerate(a))
    # >> <enumerate object at 0x....>
    print(list(enumerate(a)))
    # >> [(0,1), (1,2), (2,3), (3,4), (4,5)]
    ```

- locals

  - 로컬에 선언된 모든 변수를 조회할 수 있다
  - 디버깅에 많은 도움이 됨

