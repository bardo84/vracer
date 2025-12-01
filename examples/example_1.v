// Example 1: Simple race condition with blocking assignments
// Two counters synchronized to clock edge with assertion failure depending on execution order

`timescale 1ns / 100 ps

module race1 #(
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
        for (int i = 0; i < NUM_TESTS; i++) begin
            count1++;
            @(posedge clk);
        end

        $display("Tests completed.");
        disable generate_clock;
    end

    always @(posedge clk) begin : counter2
        count2++;
        assert (count1 == count2);
    end
endmodule
