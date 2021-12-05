%%

% read data in
close all

%dataT = readtable('2NN_dataset.csv');
%dataT = readtable('2NN_dataset_flight.5.csv');
dataT = readtable('2NN_all_dataset.csv');
data = table2array(dataT);

frame_x = data(:,1);
frame_y = data(:,2);
cart_coord_x = data(:,3);
cart_coord_y = data(:,4);

figure;
set(gcf, 'Units', 'Normalized', 'OuterPosition', [.1 .1 .8 .8]);

subplot1 = subplot(1,2,1);
plot(frame_x,frame_y,'Parent',subplot1)
%scatter(frame_x,frame_y,'Parent',subplot1)
xlim([0 512])
ylim([0 320])
xlabel('frame-x') 
ylabel('frame-y')
grid on

subplot2 = subplot(1,2,2);
plot(cart_coord_y .* 100 ,cart_coord_x .* 100)
xlim([-100 100])
ylim([-100 100])
xlabel('cart-coord-y in cm') 
ylabel('cart-coord-x in cm')
grid on

%%
% 
% scale_X = @(x) ((x-min(frame_x))./512).*max(cart_coord_x);
% scale_Y = @(x) ((x-min(frame_y))./320).*max(cart_coord_y);
% figure;
% plot(scale_X(frame_x),scale_Y(frame_y))
