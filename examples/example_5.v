// Example 5: Accumulator testbench with race condition
// Multiple processes driving inputs with blocking assignments
// Race condition occurs due to arbitrary simulation order

`timescale 1ns / 100 ps

module accum_tb_race1 #(
    parameter int NUM_TESTS = 10000,
    parameter int IN_WIDTH  = 8,
    parameter int OUT_WIDTH = 16
);
    logic clk = 1'b0;
    logic rst;
    logic en;
    logic [IN_WIDTH-1:0] data_in = '0;
    logic [OUT_WIDTH-1:0] data_out;

    accum #(
        .IN_WIDTH (IN_WIDTH),
        .OUT_WIDTH(OUT_WIDTH)
    ) DUT (
        .clk     (clk),
        .rst     (rst),
        .en      (en),
        .data_in (data_in),
        .data_out(data_out)
    );

    initial begin : generate_clock
        forever #5 clk = ~clk;
    end

    initial begin : data_in_driver
        rst = 1'b1;
        @(posedge clk);
        rst = 1'b0;
        @(posedge clk);

        forever begin
            data_in = $urandom;
            @(posedge clk);
        end
    end

    initial begin : en_driver
        en = 1'b1;
        forever begin
            @(posedge clk iff !rst);
            en = $urandom;
        end
    end

    int test = 0;
    logic [OUT_WIDTH-1:0] model = '0;

    initial begin : monitor
        @(posedge clk iff !rst);
        while (test < NUM_TESTS) begin            
            if (en) begin
                model += data_in;
                test++;
            end
            assert (data_out == model);
            @(posedge clk);
        end

        $display("Tests completed.");
        disable generate_clock;
    end
endmodule
