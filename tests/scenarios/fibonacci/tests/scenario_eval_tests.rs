use fibonacci::Fibonacci;

#[test]
fn test_fibonacci() {
    let mut fib = Fibonacci::new();
    assert_eq!(fib.next(), Some(0));
    assert_eq!(fib.next(), Some(1));
    assert_eq!(fib.next(), Some(1));
    assert_eq!(fib.next(), Some(2));
    assert_eq!(fib.next(), Some(3));
}
