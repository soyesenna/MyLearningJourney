# Generic

- [x] 1. Generic의 정의
- [x] 2. Generic의 사용법
- [x] 3. T, E, K, V, N ???
- [x] 4. Generic 와일드 카드

<br>
<br>

### 1. Generic의 정의와 사용

---
<br>

 자바에서 **제네릭**이란,Type을 Generalize한다. 컴파일 단계에서, 클래스나 메소드에서 사용할 내부 데이터 타입을 컴파일 시에 미리 지정하는 방법을 가진다. 컴파일 시에 미리 Type검사를 하게되면, 다음과 같은 장점을 가지게된다.

 1. 클래스나 메서드 내부에서 사용되는 객체의 타입 안정성을 높일 수 있다.
 2. 반환값에 대한 타입 변환 및 타입 검사에 들어가는 노력을 줄일 수 있다.

 제네릭을 사용하게 되면, 타입에 대해 추가적으로 정의를 지정해주지 않아도된다. 다음의 예시를 보며 이해해보자.

```java
 public class NodeInteger<Integer> { }
 public class NodeCharacter<Character> { }
 public class NodeString<String> { }
 public class NodeDouble<Double> { }
 ...

 public class Node<T> { }
```

 아주 간단한 예시지만, 제네릭이 가져다주는 편리함을 한 눈에 쉽게 알 수 있다. 또한 제네릭이 주는 강력함이 존재한다. 다음의 코드를 보며 이해해보자.

```java
static class A {}
static class B extends A {}
static class C extends B {}
static class D extends C {}
static class E {}
public static void main(String[] args) {
	// TODO Auto-generated method stub
	ArrayList<A> list = new ArrayList<>();
	list.add(new A());
	list.add(new B());
	list.add(new C());
	list.add(new D());
	list.add(new E()); // error
}
```

 제네릭을 이용하면, B, C, D의 ArrayList`<B, C, D>`를 생성하지 않아도 된다. (자바의 컬렉션은 대부분 제네릭이 적용되어있다), 즉 제네릭을 이용하면, 타입 변수에 대해 **다형성**을 얻을 수 있다. 

 그렇다면, 제네릭이 없었을 당시 어떻게 사용 하였을까? 우리는 어떤 타입이든 모든 것을 받을 수 있는 Class를 알고있다. 바로 Object클래스이다. 다음의 코드를 보며 이해해보자.

```java
public class Main {
    public static void main(String[] args) {
        ArrayList list = new ArrayList(); // ArrayList 생성 (제네릭 적용하지 않음)
        list.add(1); // Integer 객체 추가
        list.add("Hello"); // String 객체 추가
        list.add(3.14); // Double 객체 추가

        for (int i = 0; i < list.size(); i++) {
            Object obj = list.get(i); // ArrayList에서 객체를 가져옴 (타입은 Object)

            // 타입 변환 후 출력
            if (obj instanceof Integer) {
                int num = (Integer) obj;
                System.out.println("정수: " + num);
            } else if (obj instanceof String) {
                String str = (String) obj;
                System.out.println("문자열: " + str);
            } else if (obj instanceof Double) {
                double dbl = (Double) obj;
                System.out.println("실수: " + dbl);
            }
        }
    }
}
```

 ArrayList에 제네릭을 적용하지 않고, Object 타입으로 값을 넣었다. Integer, String, Double 등 다양한 객체를 추가할 수 있지만, 뽑을 때에는 instanceof로 타입을 체크해서, 형 변환을 해줘야 한다.

<br><br>

### 2. Generic의 사용법

---

<br>

 제네릭을 어렵게 생각하지말자, 타입이 다양하게 들어온다고 생각된다면, 타입에 T를 적어주면된다. 다음은 제네릭을 적용하는 코드의 예시이다.

```java
 public class MyArrayList0 {
	// 길이를 정해 주지 않을 때의 디폴트 사이즈 
	private static final int DEFALUT_SIZE = 10;
	
    transient int[] elementData;
    
    private static int size = 10;
    private static int counter = 0;
    
    // 어레이리스트를 만들 때, 사이즈를 인자로 주어 질 경우 
	public MyArrayList0(int size) {
		if(size > 0) {this.elementData = new int[size]; MyArrayList0.size = size;}
		else throw new IllegalArgumentException("0보다 큰 수를 적어주세요 !");
	}
	
	// 어레이리스트를 만들 때, 사이즈를 인자로 주어지지 않을 경우 
	public MyArrayList0() {
		this.elementData = new int[DEFALUT_SIZE];
		size = 10;
	}
}

public class MyArrayList2<E> {
	
	// 길이를 정해 주지 않을 때의 디폴트 사이즈 
	private static final int DEFALUT_SIZE = 10;
	
    transient Object[] elementData;
    
    private int size;
    private int counter = 0;
    
    // 어레이리스트를 만들 때, 사이즈를 인자로 주어 질 경우 
	public MyArrayList2(int size) {
		if(size > 0) {this.elementData = new Object[size]; this.size = size;}
		else throw new IllegalArgumentException("0보다 큰 수를 적어주세요 !");
	}
	
	// 어레이리스트를 만들 때, 사이즈를 인자로 주어지지 않을 경우 
	public MyArrayList2() {
		this.elementData = new Object[DEFALUT_SIZE];
		size = 10;
	}
}
```

 두개의 MyArrayList에서 어떤점이 바뀌었는지 안다면, 제네릭을 이용할 방법을 배운 것이다.

<br><br>

### 3. T, E, K, V, N ???

---

<br>

 - T : Type의 약자로, 클래스나 메서드에서 사용할 데이터 타입을 일반적으로 표현할 때 사용한다.
 - E : Element의 약자로, 컬렉션의 요소(Element) 타입을 나타내는 데 사용한다.
 - K : Key의 약자로, 맵(Map)에서 Key 값 타입을 나타내는 데 사용한다.
 - V : Value의 약자로, 맵(Map)에서 Value 값 타입을 나타내는 데 사용한다.
 - N : Number의 약자로, 숫자 타입(Number)을 나타내는 데 사용한다.

 각각의 제네릭 이름들은 쓰이는 용도에 따라 사용되는 것이고, 일반적인 규칙같은 것이다. 즉 각각의 상황에서 용도에 맞는 이름을 쓴다면, 재사용성과 안정성이 높아진다. 하지만 이렇게도 사용이 가능하다.

```java
public class MyArrayList2<짜장> {
	
    ... 중략
	public boolean addFirst(짜장 data) {
		grow();
		for(int i = counter++; i > 0; i--) {
			this.elementData[i] = this.elementData[i - 1];
		}
		this.elementData[0] = data;
		return true;
	}
	public boolean addLast(짜장 data) {
		grow();
		this.elementData[counter++] = data;
		return true;
	}
}
```

 이렇게 사용이 가능한 이유는 MyArrayList2를 생성할 때 `<Integer>`로 선언을 하면, 컴파일시에 MyArrayList2`<짜장>`에서 `짜장` -> Integer로 변환이 되기 때문이다.
<<<<<<< HEAD

<br><br>

### 4. Generic 와일드 카드

---

<br>

 Generic에서 메서드 매개변수가 어떤 타입으로 올지 모를 때, 와일드 카드를 사용한다. 일반적으로 제네릭 타입 매개변수는 하나의 타입으로 만 지정이 되지만, 와일드 카드를 사용하면, 다양한 타입의 객체를 다룰 수 있게된다.

 **<? extends T>** : T의 하위 클래스를 나타내는 와일드 카드입니다. 즉, T와 T의 자손 클래스를 모두 포함합니다. 이 경우, 해당 클래스나 인터페이스의 객체 또는 하위 클래스의 객체만 매개변수로 전달할 수 있습니다. (상한)

 **<? super T>** : T의 상위 클래스를 나타내는 와일드 카드입니다. 즉, T와 T의 조상 클래스를 모두 포함합니다. 이 경우, 해당 클래스나 인터페이스를 구현하는 객체 또는 상위 클래스의 객체만 매개변수로 전달할 수 있습니다. (하한)

 **<?>** : 제한 없이 모든 타입의 객체를 다룰 수 있는 와일드 카드입니다. 이 경우, 제네릭 타입이 사용되는 모든 곳에서 사용할 수 있지만, 주의해서 사용해야 합니다. (Collections의 addAll이나, Stream 클래스에서 map에서 다양한 타입에 대해 대응할 때 사용한다.)


```java
class A {}
class B extends A {}
class C extends A {}

public void someMethod(List<A> list) { ... } // A의 경우 만

public void someMethod(List<? extends A> list) { ... } // A, B, C
```

와일드 카드를 사용하면 제네릭 타입의 유연성과 확장성을 높일 수 있습니다. 또한, 타입 안정성을 보장해주는 효과가 있어 제네릭 매개변수를 사용할 때, 다른 타입이 하위의 메서드를 실행하는 것을 막아줍니다. 하지만, 와일드 카드를 사용할 때는 주의해서 사용해야 하며, 적절한 상황에서 사용해야 합니다.

<br><br>
