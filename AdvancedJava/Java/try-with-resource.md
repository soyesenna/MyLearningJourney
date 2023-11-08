# try-with-resource

- [x] 1. try-catch-finally
- [x] 2. try-with-resource
- [x] 3. try-catch-finally를 사용하면 안되는 이유

<br><br>

## 1. try-catch-finally

---

<br>

 try-catch-finally는 예외를 처리하기 위해서 사용한다. Java를 비롯한 많은 프로그래밍 언어에서 사용되는 예외처리 구조이다. 이를 통해 프로그램이 실행 중 발생할 수 있는 잠재적인 예외를 throw할 수 있는 코드를 작성할 수 있다.

```java
// try-catch-finally의 일반 구문
try {

} catch (Exception e1) {

} catch (Exception e2) {

} finally {

}
```

 try안 내용 중 Exception이 발생했을 때, catch구문과 맞는 Exception이면, 맞는 catch블록의 코드를 처리한다. finally 블록은 선택 사항(허나, close를 위해 강제되는 부분이기도 하다.)이며 예외 발생 여부에 관계없이 항상 실행되는 코드를 포함한다.

<br><br>

## 2. try-with-resource

---

<br>

 try-with-resource는 파일이나 데이터베이스 연결과 같이 명시적으로 닫아야 하는 리소스의 처리를 단순화하는 Java 7에 도입된 Java 기능이다. 예외가 발생하더라도 리소스가 더 이상 필요하지 않을 때 리소스가 제대로 닫히도록 한다.

 try-with-resource의 일반 구문

```java
try (ResourceType resource1 = new ResourceType(); ResourceType resource2 = new ResourceType()) {

} catch (Exception e1) {

} catch (Exception e2) {

}
```


- **리소스 관리** : 리소스를 닫는 자동 메커니즘을 제공하지 않는 반면, try-with-resource는 블록 끝에서 선언된 리소스를 자동으로 닫는다.


- **간결성** : 명시적인 리소스 종료 코드의 필요성을 제거하여 보다 간결하고 읽기 쉬운 구문을 제공하여 보다 깨끗한 코드를 만들 수 있다.

- **확장성** : 단일 try 블록에서 여러 리소스를 선언하고 관리할 수 있어 코드 구조를 단순화하므로 여러 리소스를 처리할 때 유용하다.

<br><br>

## 3. try-catch-finally를 사용하면 안되는 이유

---

<br>

 **오류가 발생하기 쉽다**, **자원을 할당하면, 항상 자원을 닫아야 한다**, **코드의 구조가 변경되면, 까먹기 쉽다.**, **가독성이 떨어진다**

 결론적으로 try-with-resource는 try-catch-finally에 비해 예외를 처리하고 리소스를 관리하는 더 간결하고 안정적인 방법을 제공한다. 리소스 관리를 간소화하고 코드 가독성을 향상시킨다 try-catch-finally를 피하면 더 깨끗하고 유지 관리가 쉬운 코드로 이어지고 리소스 누수 및 오류의 가능성을 줄일 수 있다.

<br><br>