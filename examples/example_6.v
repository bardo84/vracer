// Example 6: Non-blocking assignment explanation
// Demonstrates current vs. future values with non-blocking assignments

module nonblocking_test;
    logic clk = 1'b0;
    int x;

    initial begin
        forever #5 clk <= ~clk;
    end

    initial begin
        $timeformat(-9, 0, " ns");
        x <= 0;  // Current = 'X, Future = 0
        @(posedge clk)  // Current = Future
        x <= 1;  // Current = 0, Future = 1
        $display("%0d", x);  // Prints 0
        x <= 2;  // Current = 0, Future = 2
        $display("%0d", x);  // Prints 0
        @(posedge clk);  // Current = Future
        $display("%0d", x);  // Prints 2
    end
endmodule
