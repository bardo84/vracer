// Example 7: Non-blocking assignment order independence
// Shows that assignment order doesn't matter with non-blocking assignments
// Assertions pass regardless of order or simulation sequence

`timescale 1ns / 100 ps

module nonblocking_test2;
    logic clk = 1'b0;
    
    initial begin : generate_clock
        forever #5 clk <= ~clk;
    end

    int a1 = 0, a2 = 0, a3 = 0;
    int b1 = 0, b2 = 0, b3 = 0;
    int c1 = 0, c2 = 0, c3 = 0;

    initial begin
        for (int i = 0; i < 100; i++) begin
            for (int j = 0; j < 100; j++) begin
                a1 <= i;
                b1 <= j;
                c1 <= a1 + b1;

                a2 <= i;
                c2 <= a2 + b2;
                b2 <= j;

                c3 <= a3 + b3;
                a3 <= i;
                b3 <= j;
                @(posedge clk);
            end
        end

        $display("Tests completed.");
        disable generate_clock;
    end

    assert property (@(posedge clk) c1 == c2);
    assert property (@(posedge clk) c2 == c3);
    assert property (@(posedge clk) c1 == c3);
endmodule
