%%

% read data in
close all

%dataT = readtable('2NN_dataset.csv');
%dataT = readtable('2NN_dataset_flight.1.csv');
dataT = readtable('2NN_dataset_eval_data.csv');
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
figure;

plot(frame_x -256,frame_y -160)
xlim([-256 512/2])
ylim([-160 320/2])
xlabel('frame-x') 
ylabel('frame-y')
grid on

%%
figure;

cent_x = 0;
cent_y = 0;
r = .4;
t = 0:0.5:2*pi;
x = cent_x + r * cos(t);
y = cent_y + r * sin(t);

plot(round(x,2),round(y,2))

