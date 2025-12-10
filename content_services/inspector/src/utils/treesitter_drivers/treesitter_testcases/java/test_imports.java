package com.example.imports;

import java.util.*;
import java.io.File;
import java.io.IOException;
import static java.lang.Math.PI;
import static java.lang.Math.*;

public class ImportExamples {

    public void useImports() {
        List<String> list = new ArrayList<>();
        File file = new File("test.txt");
        double radius = 5.0;
        double area = PI * pow(radius, 2);
    }
}
