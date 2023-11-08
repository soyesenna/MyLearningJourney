# 일급 컬렉션(First Class Collection)이란?

---
일급 컬렉션은 소트웍스 앤솔로지의
[객체지향 생활체조 파트의 규칙 8](https://developerfarm.wordpress.com/2012/02/01/object_calisthenics_/)
에서 언급이 되었다고 한다.
<br>
일급 컬렉션은 **Collection**을 **Wrapping**하면서 **그 외 다른 멤버 변수가 없는 상태**를 의미한다.
<br><br>
예시를 들면 다음과 같다.

```java
List<Car> carList = new ArrayList<>();

for (String carName : carArr) {
    carList.add(new Car(carName));
}
```

다음과 같은 collection을 아래와 같이 wrapping하고 멤버 변수로 carList 하나만 가지고 있는 상태가 일급 컬렉션이다.
```java
public class Cars {
    // 멤버 변수가 하나밖에 없다는게 중요!!
    private List<Car> carList;

    public Cars(List<Car> carList) {
        this.carList = carList;
    }
```

## 그렇다면 일급 컬렉션을 왜 사용하는 걸까?
일급 컬렉션을 사용하면서 얻는 이점은 다음과 같다.
1. 비지니스에 종속적인 자료구조
2. Collection의 불변성 보장
3. 상태와 행위를 한곳에서 관리
4. 이름이 있는 컬렉션


## 1. 비지니스에 종속적인 자료구조
예를 들어 다음과 같은 조건으로 로또 복권 게임을 만든다고 하자.
+ 6개의 번호가 존재
+ 6개의 번호는 서로 중복되지 않아야함


위와 같은 조건이 있을 경우 일반적으로 서비스 메서드에서 검증과정을 거친다.<br>
구현을 해보면 다음과 같다.
```java
public class LottoService {
    private static final int LOTTO_NUMBERS_SIZE = 6;

    public void createLottoNumber() {
        List<Long> lottoNumbers = createNonDuplicateNumbers();
        validateSize(lottoNumbers);
        validateDuplicate(lottoNumbers); //이후 로직 실행
    }

    private void validateSize(List<Long> lottoNumbers) {
        if (lottoNumbers.size() != LOTTO_NUMBERS_SIZE) {
            throw new IllegalArgumentException("로또 번호는 6개만 가능합니다");
        }
    }

    private void validateDuplicate(List<Long> lottoNumbers) {
        Set<Long> nonDuplicateNumbers = new HashSet<>(lottoNumbers);
        if (nonDuplicateNumbers.size() != LOTTO_NUMBERS_SIZE) {
            throw new IllegalArgumentException("로또 번호들은 중복될 수 없습니다");
        }
    }
}
```
이러한 경우 lottoNumbers가 필요한 모든 장소에서 검증로직이 들어가야한다. 
<br>
+ List<Long>으로 된 데이터는 모두 검증 로직이 필요한지
+ 신규 입사자분들은 어떻게 이 검증로직이 필요한지 알 수 있는지

등등 모든 코드와 도메인을 알고 있지 않는다면 언제든 문제가 발생할 여지가 있다.
<br>
이러한 경우 일급 컬렉션을 사용하여 해결할 수 있다.<br>
비즈니스에 종속적인 자료구조, 즉 **주어진 조건만으로 생성할 수 있는 자료구조를 만드는 것**이다.
```java
public class LottoTicket {
    private static final int LOTTO_NUMBERS_SIZE = 6;
    private final List<Long> lottoNumbers;

    public LottoTicket(List<Long> lottoNumbers) {
        validateSize(lottoNumbers);
        validateDuplicate(lottoNumbers);
        this.lottoNumbers = lottoNumbers;
    }

    private void validateSize(List<Long> lottoNumbers) {
        if (lottoNumbers.size() != LOTTO_NUMBERS_SIZE) {
            throw new IllegalArgumentException("로또 번호는 6개만 가능합니다");
        }
    }

    private void validateDuplicate(List<Long> lottoNumbers) {
        Set<Long> nonDuplicateNumbers = new HashSet<>(lottoNumbers);
        if (nonDuplicateNumbers.size() != LOTTO_NUMBERS_SIZE) {
            throw new IllegalArgumentException("로또 번호들은 중복될 수 없습니다.");
        }
    }
}
```


## 2. Collection의 불변성 보장
일급 컬렉션은 컬렉션의 불변성을 보장한다.<br>
Java에서 final은 불변을 만들어주는 것이 아니라 재할당만 가능하다. <br> 
따라서 `final List<Car> carList;` 와 같이 선언을 하더라도 carList은 재할당만 불가능할 뿐이지 `add`, `remove`와 같은 메서드로 데이터를 추가하거나 지우는 변경작업이 가능하다.<br>
따라서 이러한 경우 일급 컬렉션과 래퍼 클래스의 방법으로 불변 객체를 생성하여 해결한다.<br>
다음과 같이 컬렉션의 값을 변경할 수 있는 메소드가 없는 컬렉션을 만들면 불변 컬렉션이 된다.
```java
public class Cars {
    // 멤버 변수가 하나밖에 없다는게 중요!!
    private List<Car> carList;

    public Cars(List<Car> carList) {
        this.carList = carList;
    }
    
    public int getCarListSize() {
        return carList.size();
    }
}
```
이 클래스의 경우 생성자와 getCarListSize() 이외에 다른 메소드가 없다.<br>
즉, 이 클래스의 사용법은 새로 만들거나 값을 가져오는 기능만 가능하다.<br>
List라는 컬렉션에 접근할 수 있는 방법이 없기 때문에 값의 변경/추가가 불가능하다.


## 3. 상태와 행위를 한곳에서 관리
일급 컬렉션의 세번째 장점은 값과 로직이 함께 존재하여 외부에서 **중복된 메서드의 생성**과 같은 문제를 해결해준다.<br>
예를 들어 여러 Pay들이 모여있고, 이 중 NaverPay 금액의 합이 필요하다고 가정하자.<br>
일반적으로 아래와 같이 작성한다.
```java
@Test
public void 로직이_밖에_있는_상태() {
        //given
        List<Pay> pays = Arrays.asList(   //값이 있는 곳
        new Pay(NAVER_PAY, 1000L),
        new Pay(NAVER_PAY, 1500L),
        new Pay(KAKAO_PAY, 2000L),
        new Pay(TOSS, 3000L));

        //when
        Long naverPaySum = pays.stream()   // 계산은 여기서
        .filter(pay -> pay.getPayType().equals(NAVER_PAY))
        .mapToLong(Pay::getAmount)
        .sum();

        //then
        assertThat(naverSum).isEqualtTo(2500L);
}
```
+ List에 데이터를 담고
+ Service 혹은 Util 클래스에서 필요한 로직 수행 

위와 같은 상황에서는 `pays`라는 컬렉션과 계산 로직은 서로 관계가 있는데, 코드로 관계를 보여주는 데에 어려움이 있다.<br>
현재 여러 타입의 Pay가 있고 특정 Pay의 합만 필요한 상황이다.
+ 값을 계산하는 로직이 여러곳에서 중복발생 가능
+ 로직 변경시 모든 곳을 다 변경해주어야함
+ 다른 Pay의 합도 필요한 경우에 코드가 흩어질 가능성이 높음 <br>

->  결론적으로 Pay의 타입에 따라 합을 게산하기 위해서는 이렇게 해야한다는 계산식을 컬렉션과 함께 두어야한다.
```java
public class PayGroups {
    private List<Pay> pays;

    public PayGroups(List<Pay> pays) {
        this.pays = pays;
    }

    public Long getNaverPaySum() {
        return pays.stream()
                .filter(pay -> PayType.isNaverPay(pay.getPayType()))
                .mapToLong(Pay::getAmount)
                .sum();
    }
}
```
만약 다른 결제 수단들의 합도 필요하다면 아래와 같이 리팩토링이 가능하다.

```java
public class PayGroups {
    private List<Pay> pays;

    public PayGroups(List<Pay> pays) {
        this.pays = pays;
    }

    public Long getNaverPaySum() {
        return getFilteredPays(pay -> payType.isNaverPay(pay.getPayType()));
    }

    public Long getKakaoPaySum() {
        return getFilteredPays(pay -> payType.isKakaoPay(pay.getPayType()));
    }

    private Long getFilteredPays(Predicate<Pay> predicate) {
        return pays.stream()
                .filter(predicate)
                .mapToLong(Pay::getAmount)
                .sum();
    }
}
```
이렇게 PayGroups라는 일급 컬렉션이 생김으로서 상태와 로직이 한곳에서 관리된다.

## 4. 이름이 있는 컬렉션
마지막 장점은 **컬렉션에 이름을 붙일 수 있다**는 것이다.<br>
같은 Pay들의 모임이지만 네이버페이의 List와 카카오페이의 List는 다르다.<br>
그렇다면 이 둘을 구분하기 위해서 가장 흔히 하는 방법은 변수명을 다르게 하는 것이다.<br>
```java
@Test
public void 컬렉션을_변수명으로(){
    // given
    List<Pay> naverPays = createNaverPays();
    List<Pay> kakaoPays = createKakaoPays();
    // when

    // then
}
```
+ **검색이 어렵다.**<br>
네이버페이 그룹이 어떻게 사용되는지 검색 시 변수명으로만 검색할 수 있다.
이 상황에서는 검색이 불가능하다.<br>
네이버페이의 그룹이라는 뜻은 개발자마다 다르게 지을 수 있기 때문이다.
+ **명확한 표현이 불가능하다.**<br>
변수명에 불과하기 때문에 의미 부여가 어렵다.

```java
@Test
public void 일급컬렉션의_이름으로() {
    //given
    NaverPays naverPays = new NaverPays(createNaverPays());
    KakaoPays kakaoPays = new KakaoPays(createKakaoPays());
    // when
    // then
}
```
위와 같이 작성하면 좀 더 명확한 표현이 가능하고 컬렉션 클래스를 검색하면 모든 사용코드를 찾아낼 수 있다. <br><br>

---
참고
---
[일급 컬렉션 (First Class Collection)의 소개와 써야할 이유](https://jojoldu.tistory.com/412)















