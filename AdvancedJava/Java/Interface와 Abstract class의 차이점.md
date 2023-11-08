# Interface와 Abstract class의 차이점

- [x] 1. Interface란?
- [x] 2. Abstract class란?
- [x] 3. Interface와 Abstract class의 차이점은?
- [x] 4. 결론
<br><br>

### 1. Interface란?

---

<br>

#### Interface의 정의

 인터페이스는 서비스 공급자와 자신의 객체가 해당 서비스를 사용할 수 있게 하려는 클래스가 있을 때, 이 두 클래스 사이의 계약을 표현하는 메커니즘이 인터페이스이다. 즉 객체 간의 상호작용을 정의하기 위한 추상 타입이며, 인터페이스는 메서드 시그니처만을 정의하고, 해당 메서드들은 구현되는 클래스에서 반드시 인터페이스에 정의된 메서드들을 모두 구현해야 한다.

#### Interface를 사용할 때의 장점

 인터페이스는 일종의 계약(Contract)으로도 볼 수 있다. 인터페이스를 사용하는 객체는 인터페이스가 제공하는 메서드를 반드시 구현해야 하며, 이를 통해 **다형성**과 **결합도**를 낮출 수 있습니다. 또한, 인터페이스를 이용하여 여러 클래스에서 공통적으로 사용하는 기능을 정의하고, 이를 구현하는 클래스들은 각자의 방식으로 구현함으로써 코드의 재사용성과 유지보수성을 높일 수 있다.


#### 자바 8이후의 Interface

 인터페이스는 다른 인터페이스를 상속받을 수 있으며, 다중 상속도 가능하다. 또한, 자바 8부터는 디폴트 메서드(default method)와 정적 메서드(static method)를 인터페이스에 추가할 수 있게 되어 더욱 유연한 인터페이스의 활용이 가능해졌다.

```java
public interface List<E> extends Collection<E> {
    // ...
}
```

#### 디폴트 메서드, 정적 메서드?

 디폴트 메서드와 정적 메서드는 인터페이스에서 구현한 메서드이다. 정적 메서드는 인터페이스 내부에서 구현이 되어있기 때문에, 상속을 받는 경우, 정적 메서드를 수정할 수 없다. 허나 디폴트 메서드는 인터페이스에서 구현된 것을 오버라이드하여 구현된걸 재정의하거나 그대로 사용할 수 있다. 정적 메서드는 인터페이스를 구현하지 않는 클래스에서도 사용이 가능하기 때문에, 보다 더 쉽고 간단하게 유틸리티 인터페이스를 만들 수 있게 되었다.

```java
public interface Animal {
    // 인터페이스에서 정적 메서드 선언
    static int getNumberOfLegs() {
        return 4;
    }

    // 인터페이스에서 디폴트 메서드 구현
    default void makeSound() {
        System.out.println("The animal makes a sound.");
    }
}

public class Dog implements Animal {
    // makeSound 메서드를 오버라이드
    @Override
    public void makeSound() {
        System.out.println("The dog barks.");
    }
}

public class Main {
    public static void main(String[] args) {
        // 인터페이스의 정적 메서드 호출
        System.out.println("Number of legs: " + Animal.getNumberOfLegs());

        // 인터페이스의 디폴트 메서드 호출
        Animal animal = new Dog();
        animal.makeSound();
    }
}

```

<br><br>


### 2. Abstract class란?

---

<br>

#### Abstract class 정의

 추상 클래스(Abstract class)란, 구현부가 없는(미완성인) 추상 메서드(abstract method)를 가지고 있는 클래스를 말한다. 추상 클래스는 다른 클래스에서 상속을 받아 기능을 확장하도록 하는 용도로 사용된다. 추상 클래스는 클래스의 일부 기능을 구현하고, 일부 기능을 하위 클래스에서 구현하도록 하는 경우에 사용된다.

 추상 클래스는 **abstract** 키워드를 사용하여 정의할 수 있다. 추상 클래스는 인스턴스를 생성할 수 없고, 하위 클래스에서 상속받아 구현한 후에야 인스턴스를 생성할 수 있습니다. 추상 클래스는 하나 이상의 추상 메서드를 가지고 있어야 한다. 추상 메서드는 메서드의 시그니처만 있고, 구현부가 없는 메서드를 말한다. 이 추상 메서드를 하위 클래스에서 구현하도록 강제한다.

 추상 클래스는 일반 클래스와 마찬가지로 필드, 생성자, 일반 메서드를 가질 수 있다. 추상 클래스는 일반 클래스와 달리 하나 이상의 추상 메서드를 가지므로, 하위 클래스에서는 추상 메서드를 구현하는 것을 강제된다. 추상 클래스는 자바에서 상속, 다형성과 같은 개념을 구현하는 데에 있어서 매우 중요한 역할이다.

```java
abstract class Shape {
   // 추상 메서드
   public abstract void draw();
   
   // 일반 메서드
   public void fill() {
      System.out.println("Shape filled with color");
   }
}

class Rectangle extends Shape {
   public void draw() {
      System.out.println("Rectangle drawn");
   }
}

class Circle extends Shape {
   public void draw() {
      System.out.println("Circle drawn");
   }
}

public class Main {
   public static void main(String[] args) {
      Shape s1 = new Rectangle();
      s1.draw();
      s1.fill();
      
      Shape s2 = new Circle();
      s2.draw();
      s2.fill();
   }
}

```

#### Abstract class 장점

 추상 클래스는 상속을 통해 하위 클래스에서 구현을 **강제**할 수 있는 추상 메서드를 가질 수 있기 때문에, 객체 지향 프로그래밍에서 **다형성**을 구현하는 데에 유용하다.

 추상 클래스를 사용하면, 상속 받은 하위 클래스들은 추상 클래스에서 정의한 메서드들을 구현하게 되고, 이를 통해 다양한 하위 클래스들이 추상 클래스를 상속받아 공통된 메서드를 구현하더라도 각 하위 클래스는 자신만의 구체적인 구현을 가질 수 있다.

 추상 클래스는 또한 인스턴스화 되지 않기 때문에, 추상 클래스를 이용하여 추상화를 통해 공통된 개념을 나타낼 수 있다.

<br><br>

### 3. Interface와 Abstract class의 차이점은?

---

<br>


 인터페이스는 해당 인터페이스를 구현(implement)하는 클래스가 반드시 가져야 하는 메서드들의 선언(declaration)을 포함한 일종의 규약(specification)이다.

 추상 클래스는 일반 클래스와 마찬가지로 데이터 필드와 메서드를 가지고 있지만, 하나 이상의 추상 메서드를 포함하여 클래스 자체의 완전한 구현을 갖추지 않은 불완전한 클래스다.

 인터페이스는 여러 클래스들 간에 공통된 특징을 추상화하여 정의할 수 있다. 이를 통해 다중 상속과 같은 기능을 제공하고, 높은 결합도를 갖는 코드를 방지하며, 객체지향 설계의 기본 개념 중 하나인 다형성(polymorphism)을 구현하는 데 활용된다.

 추상 클래스는 하위 클래스에 공통적인 메서드와 필드를 추출하여 부모 클래스로 정의하고, 하위 클래스에서 상속받아 구체화할 수 있도록 한다. 이를 통해 코드의 재사용성과 유지보수성을 높일 수 있다. 또한, 추상 클래스를 상속받은 하위 클래스는 해당 추상 클래스의 추상 메서드를 반드시 구현해야 하므로, 일종의 규약으로서의 역할을 수행한다.

<br><br>

### 4. 결론

---

<br>

 Interface와 Abstract class 모두 클래스 간의 상속과 다형성을 구현하는 데 활용되며, 인터페이스는 규약(규칙)을 정의하는데 중점을 두고, 추상 클래스는 구체화될 필요가 있는 공통적인 메서드와 필드를 정의하는데 중점을 둔다. 

 - **구현 여부** : ~~인터페이스는 대부분의 메소드가 추상 메소드이므로 구현이 강제된다. 하지만 추상 클래스는 추상 메소드뿐 아니라 구현된 메소드도 포함될 수 있다.~~ 자바 8 이후로는 다르게 생각해야한다.
 
 - **다중 상속** : 인터페이스는 다중 상속이 가능하다. 하지만 추상 클래스는 단일 상속만을 지원한다.
 
 - **인스턴스 생성** : 인터페이스는 객체 생성이 불가능하다. 하지만 추상 클래스는 객체 생성이 가능하다.
 
 - **목적** : 인터페이스는 객체의 동작 방식을 표준화하기 위해 사용된다. 하지만 추상 클래스는 공통적인 속성을 묶기 위해 사용된다.