## 클래스란?(class)

<br>

클래스는 객체를 만들어 내기 위한 설계도로 그 안에 객체의 상태를 나타내는 필드(field)와 객체의 행동을 나타내는 메소드(method)로 구성된다

<br>

## 객체란?(Object)

구현할 대상으로 클래스에 선언된 모양 그대로 생성된 실체이다. ‘클래스의 인스턴스’ 라고도 불리는데 그 이유는 인스턴스에서 자세히 알수있다

<br>

```java
public class Person{
    //필드(field)
    String name;
    int age;
    char sex;
    
    //생성자(Constructor)
    Person(String name, int age, char sex){
        this.name = name;
        this.age = age;
        this.sex = sex;
    }
    
    //메소드(method)
    void eat(){
        System.out.println("냠냠..");
    }
    
    void walk(){
        System.out.println("뚜벅뚜벅");
    }
    
    void sleep(){
        System.out.println("zzz...");
    }
}
```

<br>

![[https://velog.io/@dongvelop/Java-클래스-객체-인스턴스의-차이](https://velog.io/@dongvelop/Java-%ED%81%B4%EB%9E%98%EC%8A%A4-%EA%B0%9D%EC%B2%B4-%EC%9D%B8%EC%8A%A4%ED%84%B4%EC%8A%A4%EC%9D%98-%EC%B0%A8%EC%9D%B4)](https://velog.velcdn.com/images/dongvelop/post/22a5ab00-c09f-4fc1-8709-89c4ff988370/image.png)

[https://velog.io/@dongvelop/Java-클래스-객체-인스턴스의-차이](https://velog.io/@dongvelop/Java-%ED%81%B4%EB%9E%98%EC%8A%A4-%EA%B0%9D%EC%B2%B4-%EC%9D%B8%EC%8A%A4%ED%84%B4%EC%8A%A4%EC%9D%98-%EC%B0%A8%EC%9D%B4)

<br>

## 인스턴스란?(Instance)

클래스를 바탕으로 소프트웨어 세계에 구현된 구체적 실체를 말한다. 

객체를 소프트웨어에 실체와 하면 ‘인스턴스’라 부르는데 실체화된 인스턴스는 메모리에 할당된다

인스턴스는 객체에 포함된다 볼수 있는데. 객체 지향 프로그래밍 관점(oop)에서 볼때 객체가 메모리에 할당되어 실제 사용될 때 ‘인스턴스’라 부른다

추상적인 개념과 구체적 객체사이에 초점을 맞출 때 사용하는데
인스턴스는 어떤 원본(추상적 개념)으로 부터 ‘생성된 복제본’을 의미한다

```java
public class PersonTest{
    public static void main(String[] args){
        // 객체 생성 = 인스턴스
        Person p1 = new Person("코디빌더", "20", "M"); 
        Person p2 = new Person("티스토리", "20", "F");
        
        // 메소드 사용
        p1.eat();
        p1.walk();
        p1.sleep();
        
        p2.eat();
        p2.walk();
        p2.sleep();
    }
}
```

<br>

ex). 붕어빵 틀, 붕어빵, 붕어빵(음식)

- 클래스
    
    ![붕어빵틀](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https://t1.daumcdn.net/cfile/tistory/99DAE4485BD1051103)
    

- 인스턴스
    
    ![Untitled](./image/%EB%B6%95%EC%96%B4%EB%B9%B5%EB%93%A4.png)
    
    인스턴스는 붕어빵
    

- 객체
    
    ![Untitled](./image/%EB%93%A4%EA%B3%A0%EC%9E%88%EB%8A%94%20%EB%B6%95%EC%96%B4%EB%B9%B5.png)
    
    객체는 붕어빵이라는 음식
    

객체와 인스턴스 의견

![Untitled](./image/class%20%EA%B0%9D%EC%B2%B4%20%EC%9D%98%EA%B2%AC%201.png)

![Untitled](./image/class%EA%B0%9D%EC%B2%B4%20%EC%9D%98%EA%B2%AC%202.png)

<br>

---

<br>

참고

- https://www.slipp.net/questions/126 **객체, 클래스, 인스턴스의 차이점은?(여러 견해들)**
- https://scorpio-mercury.tistory.com/1 붕어빵 예시