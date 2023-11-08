# Anntation

- [x] 1. Annotation 무엇인가?
- [x] 2. 어디에, 어떻게 Annotation를 사용할까?

<br><br>

### 1. Annotation 무엇인가?

---
<br>

 Annotation은 주석처럼, 프로그래밍 언어에 영향을 미치지 않으며, 유용한 정보를 제공한다. 코드를 작성할 때, 컴파일전, 문법 에러를 체크할 수 있고, 빌드나 배포시 코드를 자동으로 생성할 수 있도록 정보 제공을 해준다. 특정 기능을 실행하도록 정보를 제공해주기도 한다.

 예전 자바에서 소스코드를 작성할 때, 프로그램에 대한 문서를 따로 작성하게 되었다. 즉 Class 또는 Method에 대한 정보를 따로 문서 작성하게 되니, 소스코드와 문서와의 불일치가 발생하게 되었다. 그래서, 소스코드와 문서와 합쳐 /* */(javadoc)주석을 이용해서, 작성하게 되었다.

 Annotation은 소스코드와 XML 파일(설정 파일)의 경우도 서로 분리되어있다 보니, 둘 간의 불일치가 자주 발생하게 되었고, 소스코드와 XML 파일(설정 파일)을 합쳐, Annotation이 생겨나게 되었다.

 Annotation은 Junit이라는 특정 프로그램을 위해, 정보를 제공하기위해 생겨났다. 예를 들어 @Test와 같이 프로그램에 설정 정보를 심게 되었다. 다음의 표는 자바에서 제공하는 Annotation으로 *가 붙은 것은 메타 애너테이션이다. 
 
 메타 Annotation은 Annotation을 만들 때 사용한다. 

 | Annotation | 설명                                          |
 |------------|----------------------------------------------|
 | @Override  | 컴파일러에게 오버라이딩을 하는 메서드라는 것을 알린다.    |
 | @Deprecaled| 앞으로 사용하지 않을 것을 권장하는 대상에 붙인다.       |
 | @SuppressWarnings | 컴파일러의 특정 경고메시지가 나타나지 않게 해준다.|
 | @SafeVarargs| 제네릭 타입의 가변인자에 사용한다.                  |
 | @FunctionalInterface| 함수형 인터페이스라는 것을 알린다.          |
 | @Native    | native메서드에서 참조되는 상수 앞에 붙인다.          |
 | @Target*   | Annotation이 적용가능한 대상을 지정하는데 사용한다.      |
 |@Documented*| Annotation 정보가 javadoc으로 작성된 문서에 포함되게 한다.|
 |@Inherited*| Annotation 자손 클래스에 상속이 되도록 한다.            |
 |@Retention*| Annotation이 유지되는 범위를 지정하는데 사용한다.        |
 |@Repeatable*| Annotation을 반복해서 적용할 수 있게 한다.            |  

 

<br><br>

### 2. 어디에, 어떻게 Annotation을 사용할까?

---

 Annotation을 직접 커스텀화 시킬 수 있다. Annotation의 메서드는 추상 메서드ㅣ며, Annotation을 적용할 때 지정(순서X)한다. Annotation의 메서드는 추상 메서드이므로, 구현이 필요 없다.

```java
 @interface AnnotationName {
    // Annotation의 요소를 선언한다.
    Type elementName();
 }

 // 예시
 @interface DateTime {
    // abstract method
    String yymmdd();
    Stirng hhmmss();
 }

 // 사용 예시
 @DateTime(
    yymmdd = "230415",
    hhmmss = "013032"
 )
 public class clazz { ... }

 // 또한 Annotation안에 Annotation을 사용할 수 있다.
 @interface TestInfo {
    int count();
    String testedBy();
    String[] testTools();
    TestType testType(); // Enum TestType = {FIRST, FINAL}
    DateTime testDate(); // This!
 }

 // 사용 예시
 @TestInfo(
    count = 3,
    testedBy = "wonho",
    testTools = {"Junit", "AutoTester"},
    testType = TestType.FIRST,
    testDate = @DateTime(yymmdd = "230415", hhmmss = "013032")
 )
 public class newClass { ... }

 // Annotation은 적용시 값을 지정하지 않으면, 사용될 수 있는 default값이 사용된다.
 @interface TestInfo {
    int count() default 1;
 }
 @TestInfo // @TestInfo(count = 1)과 동일
 public class newClass { ... }

 // 요소가 하나이고, 메서드 이름이 value일 때는 요소의 이름을 생략할 수 있다.
 @interface TestInfo {
    String value();
 }
 @TestInfo("passed") // @TestInfo(value="passed")와 같다.
 public class newClass { ... }

 // 요소의 타입이 배열인 경우 값이 하나가 아닌 경우 {}로 감싸줘야 한다.
 @interface TestInfo {
    String[] testTools();
 }
 @TestInfo(testTools={"Junit", "AutoTester"})
 @TestInfo(testTools="Junit")
 @TestInfo(testTools={}) // 값이 없을 때는 {}가 필요하다.


```

 모든 Annotation의 조상은 interface Annotation이다. 하지만, 상속은 불가능 하다. 코드를 통해 봐보자.

```java
 @interface TestInfo extends Annotation { // <- extends Annotation 에러를 일으킨다. 하지만, 상속을 받지는 않지만 Annotation 인터페이스의 추상 메서드를 구현하지 않고도 사용이 가능하다.
    ...
 }

 package java.lang.annotation;

 public interface Annotation { // Annotation 자신은 인터페이스이다.
    boolean equals(Object obj);
    int hashCode();
    String toString();

    Class<? extends Annotation> annotationType(); // 애너테이션의 타입을 반환
    // 하지만, Annotation의 interface에 있는 추상 메서드를 구현하지 않아도 사용이 가능하다. 컴파일러가 자동으로 메서드를 추가해 주기 때문이다.
 }
```

 Marker Annotation으로 요소가 하나도 정의 되지 않은 Annotation을 의미한다.

```java
 @Target(ElementType.METHOD)
 @Retention(RetentionPolicy.SOURCE)
 public @interface Override {} // Marker Annotation 정의된 요소가 없다.

 @Target(ElementType.METHOD)
 @Retention(RetentionPolicy.SOURCE)
 public @interface Test {} // Marker Annotation 정의된 요소가 없다.

 // 따라서 정의 된게 없으므로, 그냥 붙이면 된다.
 @Test // 이 메서드가 테스트 대상임을 테스트 프로그램(Junit)에게 알린다.
 public void method() { ... }

 @Deprecated
 public int getdate() { ... }
```

 Annotation 요소의 규칙을 지켜야 한다. 요소의 타입은 기본형, String, enum, Annotation, Class(설계도 객체)만 허용된다. ( )안에 매개 변수를 선언할 수 없으며, 예외를 선언할 수 없다. 요소를 타입 매개 변수로 정의할 수 없다. 다음의 코드를 보고 잘못된 부분을 찾아보자.

```java
 @interface AnnoTest {
    int id = 100; 
    String major (int i, int j); // 매개변수를 선언할 수 없다.
    String minor () throws Exception; // 예외를 던질 수 없다.
    ArrayList<T> list(); // 요소를 타입 매개 변수로 정의할 수 없다.
 }
```
