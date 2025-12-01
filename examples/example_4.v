// Example 4: Simple accumulator module with enable and reset
// DUT used in accumulator testbench examples

module accum #(
    parameter int IN_WIDTH  = 16,
    parameter int OUT_WIDTH = 32
) (
    input  logic                 clk,
    input  logic                 rst,
    input  logic                 en,
    input  logic [ IN_WIDTH-1:0] data_in,
    output logic [OUT_WIDTH-1:0] data_out
);
    always_ff @(posedge clk) begin
        if (en) data_out <= data_out + data_in;
        if (rst) data_out <= '0;
    end
endmodule
