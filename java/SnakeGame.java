import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.Random;

public class SnakeGame extends JPanel implements ActionListener, KeyListener {
    private final int TILE_SIZE = 25;
    private final int GRID_WIDTH = 20;
    private final int GRID_HEIGHT = 20;
    private final int DELAY = 150; // speed

    private int[] x = new int[GRID_WIDTH * GRID_HEIGHT];
    private int[] y = new int[GRID_WIDTH * GRID_HEIGHT];
    private int snakeLength;
    private int foodX, foodY;
    private int direction; // 0=up, 1=right, 2=down, 3=left
    private boolean running = false;
    private Timer timer;
    private int score = 0, bestScore = 0;

    // Customizable colors
    private Color snakeColor = Color.GREEN;
    private Color foodColor = Color.RED;
    private Color bgColor = Color.BLACK;

    public SnakeGame() {
        setPreferredSize(new Dimension(GRID_WIDTH * TILE_SIZE, GRID_HEIGHT * TILE_SIZE));
        setBackground(bgColor);
        setFocusable(true);
        addKeyListener(this);
        startGame();
    }

    private void startGame() {
        snakeLength = 3;
        for (int i = 0; i < snakeLength; i++) {
            x[i] = GRID_WIDTH / 2 - i;
            y[i] = GRID_HEIGHT / 2;
        }
        direction = 1; // start right
        placeFood();
        score = 0;
        running = true;
        timer = new Timer(DELAY, this);
        timer.start();
    }

    private void placeFood() {
        Random rand = new Random();
        foodX = rand.nextInt(GRID_WIDTH);
        foodY = rand.nextInt(GRID_HEIGHT);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);

        if (running) {
            // Food
            g.setColor(foodColor);
            g.fillOval(foodX * TILE_SIZE, foodY * TILE_SIZE, TILE_SIZE, TILE_SIZE);

            // Snake
            for (int i = 0; i < snakeLength; i++) {
                g.setColor(snakeColor);
                g.fillRect(x[i] * TILE_SIZE, y[i] * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            }

            // Score
            g.setColor(Color.WHITE);
            g.drawString("Score: " + score + "  Best: " + bestScore, 10, 15);

        } else {
            gameOver(g);
        }
    }

    private void gameOver(Graphics g) {
        g.setColor(Color.RED);
        g.setFont(new Font("Arial", Font.BOLD, 30));
        g.drawString("Game Over", getWidth()/2 - 75, getHeight()/2);
        g.setFont(new Font("Arial", Font.PLAIN, 16));
        g.drawString("Press SPACE to Restart", getWidth()/2 - 90, getHeight()/2 + 30);
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        if (running) {
            move();
            checkFood();
            checkCollision();
        }
        repaint();
    }

    private void move() {
        for (int i = snakeLength - 1; i > 0; i--) {
            x[i] = x[i-1];
            y[i] = y[i-1];
        }

        switch (direction) {
            case 0: y[0]--; break; // up
            case 1: x[0]++; break; // right
            case 2: y[0]++; break; // down
            case 3: x[0]--; break; // left
        }
    }

    private void checkFood() {
        if (x[0] == foodX && y[0] == foodY) {
            snakeLength++;
            score++;
            if (score > bestScore) bestScore = score;
            placeFood();
        }
    }

    private void checkCollision() {
        // Border collision
        if (x[0] < 0 || x[0] >= GRID_WIDTH || y[0] < 0 || y[0] >= GRID_HEIGHT) {
            running = false;
            timer.stop();
        }

        // Self collision
        for (int i = snakeLength - 1; i > 0; i--) {
            if (x[0] == x[i] && y[0] == y[i]) {
                running = false;
                timer.stop();
            }
        }
    }

    @Override
    public void keyPressed(KeyEvent e) {
        int key = e.getKeyCode();

        if ((key == KeyEvent.VK_LEFT || key == KeyEvent.VK_A) && direction != 1) {
            direction = 3;
        } else if ((key == KeyEvent.VK_RIGHT || key == KeyEvent.VK_D) && direction != 3) {
            direction = 1;
        } else if ((key == KeyEvent.VK_UP || key == KeyEvent.VK_W) && direction != 2) {
            direction = 0;
        } else if ((key == KeyEvent.VK_DOWN || key == KeyEvent.VK_S) && direction != 0) {
            direction = 2;
        } else if (key == KeyEvent.VK_SPACE && !running) {
            startGame();
        }
    }

    @Override public void keyReleased(KeyEvent e) {}
    @Override public void keyTyped(KeyEvent e) {}

    public static void main(String[] args) {
        JFrame frame = new JFrame("Snake Game - Java");
        SnakeGame game = new SnakeGame();
        frame.add(game);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.pack();
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }
}
