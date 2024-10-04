import java.util.Scanner;

public class StudentCode {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int n = scanner.nextInt();
        System.out.println(n * n);
        scanner.close();
    }
}