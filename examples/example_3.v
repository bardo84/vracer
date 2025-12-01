// Example 3: Debug version of race2 with display statements
// Shows actual simulation order and demonstrates race condition occurrence

`timescale 1ns / 100 ps

module race2_debug #(
    parameter int NUM_TESTS = 100,
    parameter int WIDTH = 8
);
    logic clk = 1'b0;
    logic [WIDTH-1:0] count1 = '0;
    logic [WIDTH-1:0] count2 = '0;

    initial begin : generate_clock
        forever #5 clk = ~clk;
    end

    initial begin : counter1
        $timeformat(-9, 0, " ns");

        for (int i = 0; i < NUM_TESTS; i++) begin
            count1++;
            $display("[%0t] count1 = %0d", $realtime, count1);
            @(posedge clk);
        end

        $display("Tests completed.");
        disable generate_clock;
    end

    initial begin : counter2
        forever begin
            @(posedge clk);
            count2++;
            $display("[%0t] count2 = %0d", $realtime, count2);
            assert (count1 == count2);
        end
    end
endmodule
